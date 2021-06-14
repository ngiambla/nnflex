'''ntile.py

'''
from collections import OrderedDict

from accelerators.nacl.npe import NPE

from core.defines import Operator
from core.pe import PE
from core.tile import Tile
from core.compackets import *
from core.interconnect import Interconnect


class NTilePacketProc():
    '''
    '''
    SEND_READ = 1
    WAIT_FOR_READ = 2
    DISPATCH = 3
    WAIT_FOR_PE = 4
    WRITE_BACK = 5
    WAIT_FOR_WRITE_ACK = 6
    SEND_ACK = 7
    TERMINATE = 8

    def __init__(self, mem, tile_packet):
        self._mem = mem
        self._tile_packet = tile_packet
        # First, grab the tile packet ID
        self._tile_packet_id = hex(id(self._tile_packet))

        # Parse the first operand of the TilePacket
        source = self._tile_packet.destination_device()
        #source, destination, packet_id, seq_num, address
        self._read_req_op1 = MemReadPacket(source, self._mem, self._tile_packet_id, 0, self._tile_packet.op1_addr())
        self._read_req_op1_sent = False
        self._read_resp_op1 = None

        # Parse the second operand of the TilePacket
        self._read_req_op2 = MemReadPacket(source, self._mem, self._tile_packet_id, 1, self._tile_packet.op2_addr())
        self._read_req_op2_sent = False
        self._read_resp_op2 = None

        self._pe_packet_sent = False
        self._pe_packet_resp = None

        self._mem_write_packet = None

        self._current_stage = self.SEND_READ
        self._next_stage = self.SEND_READ


    def update_stage(self):
        self._current_stage = self._next_stage      
        return self._current_stage



    def send_read_reqs(self, interconnect):
        '''
        '''
        if self._current_stage != self.SEND_READ:
            return

        self._next_stage = self.SEND_READ
        if not self._read_req_op1_sent:
            self._read_req_op1_sent = interconnect.send(self._read_req_op1)

        if not self._read_req_op2_sent:
            self._read_req_op2_sent = interconnect.send(self._read_req_op2)

        if self._read_req_op1_sent and self._read_req_op2_sent:
            self._next_stage = self.WAIT_FOR_READ


    def listen_for_read_response(self,mem_ack_packet):
        '''
        '''
        if self._current_stage != self.WAIT_FOR_READ:
            return False

        if self._tile_packet_id == mem_ack_packet.get_packet_id():
            if mem_ack_packet.get_seq_num() == 0:
                self._read_resp_op1 = mem_ack_packet
                return True
            if mem_ack_packet.get_seq_num() == 1:
                self._read_resp_op2 = mem_ack_packet
                return True
        return False

    def handle_read_response(self):
        if self._current_stage != self.WAIT_FOR_READ:
            return

        self._next_stage = self.WAIT_FOR_READ

        if self._read_resp_op1 is not None and self._read_resp_op2 is not None:
            self._next_stage = self.DISPATCH

    def dispatch_to_PE(self, interconnect, PE):
        if self._current_stage != self.DISPATCH:
            return False

        self._next_stage = self.DISPATCH

        if self._read_resp_op1 is None or self._read_resp_op2 is None:
            return False

        op1 = self._read_resp_op1.content()
        op2 = self._read_resp_op2.content()
        operation = self._tile_packet.operation()
        source = self._tile_packet.destination_device()
 
        PE_packet = PEReqPacket(source, PE, self._tile_packet_id, 0, op1, op2, operation)
 
        if interconnect.send(PE_packet):
            self._pe_packet_sent = True
            self._next_stage = self.WAIT_FOR_PE
            return True

        return False

    def listen_for_PE_response(self, PE_response_packet):
        if self._current_stage != self.WAIT_FOR_PE:
            return False

        self._next_stage = self.WAIT_FOR_PE

        if PE_response_packet.get_packet_id() != self._tile_packet_id:
            return False
        
        self._pe_packet_resp = PE_response_packet
        self._next_stage = self.WRITE_BACK
        return True

    def write_result(self, interconnect):
        if self._current_stage != self.WRITE_BACK:
            return

        self._next_stage = self.WRITE_BACK

        res_addr = self._tile_packet.res_addr()
        if interconnect.send(MemWritePacket(self._tile_packet.destination_device(), self._mem, self._tile_packet_id, 0, res_addr, self._pe_packet_resp.result())):
            self._next_stage = self.WAIT_FOR_WRITE_ACK


    def wait_for_memwrite_ack(self, mem_write_ack_packet):
        if self._current_stage != self.WAIT_FOR_WRITE_ACK:
            return False

        self._next_stage = self.WAIT_FOR_WRITE_ACK
        if mem_write_ack_packet.get_packet_id() == self._tile_packet_id:
            self._next_stage = self.SEND_ACK
            return True

        return False



    def send_ack_to_sys(self, interconnect):
        if self._current_stage != self.SEND_ACK:
            return 

        self._next_stage = self.SEND_ACK
        src = self._tile_packet.destination_device()
        dst = self._tile_packet.source_device()
        if interconnect.send(TileRespPacket(src, dst, self._tile_packet.get_packet_id())):
            self._next_stage = self.TERMINATE




class NTile(Tile): 

    def __init__(self, system_clock_ref, device_interconnect, data_queue_size, tile_packet_interconnect, tile_packet_queue_size, offchip_memory, num_pe_rows = 1, num_pe_cols = 1):
        Tile.__init__(self, system_clock_ref, device_interconnect, data_queue_size)

        # Handling TilePacket Requests
        self._tile_packet_processor_queue = list()
        self._tile_packet_interconnect = tile_packet_interconnect
        self._tile_packet_interconnect.add_connection(self)

        self._offchip_memory = offchip_memory
 
        # Create a local interconnect.
        # self._local_interconnect = Interconnect(self._system_clock_ref)

        # # Create a local memory to buffer data.
        # self._local_memory = Memory()

        # # Add the memories to the local interconnect
        # self._local_interconnect.add(self._local_memory)

        # From the initialization parameters, 
        self._num_pe_rows = num_pe_rows
        self._num_pe_cols = num_pe_cols
        self._pe_grid = [[NPE(self._system_clock_ref, device_interconnect)]*self._num_pe_cols for i in range(self._num_pe_rows)]

        # To handle more than 1 packet at a time.
        self._packet_buffer = list()
        self._packet_size = 2



    def process(self):


        self._fetch_tile_packets()
        self._fetch_comm_packets()

        packets_to_remove = set()
        processors_to_remove = set()


        for i in range(len(self._tile_packet_processor_queue)):
            packet_processor = self._tile_packet_processor_queue[i]
            proc_stage = packet_processor.update_stage()

            # Remove the processor.
            if proc_stage == NTilePacketProc.TERMINATE:
                processors_to_remove.add(i)
                continue

            if proc_stage == NTilePacketProc.SEND_READ:
                packet_processor.send_read_reqs(self._interconnect)
                continue

            if proc_stage == NTilePacketProc.WAIT_FOR_READ:  
                for j in range(len(self._packet_buffer)):
                    packet = self._packet_buffer[j]
                    if isinstance(packet, MemReadAckPacket):
                        if packet_processor.listen_for_read_response(packet):
                            packets_to_remove.add(j)
                packet_processor.handle_read_response()
                continue

            if proc_stage == NTilePacketProc.DISPATCH:
                pe_hit = False            
                for i in range(self._num_pe_rows):
                    for j in range(self._num_pe_cols):
                        # get PE.
                        if packet_processor.dispatch_to_PE(self._interconnect, self._pe_grid[i][j]):
                            pe_hit = True 
                            break
                    if pe_hit:
                        break
                continue

            if proc_stage == NTilePacketProc.WAIT_FOR_PE:
                #listen_for_PE_response
                for j in range(len(self._packet_buffer)):
                    packet = self._packet_buffer[j]
                    if isinstance(packet, PERespPacket):     
                        if packet_processor.listen_for_PE_response(packet):
                            packets_to_remove.add(j)
                            break
                continue

            if proc_stage == NTilePacketProc.WRITE_BACK:
                packet_processor.write_result(self._interconnect)
                continue

            if proc_stage == NTilePacketProc.WAIT_FOR_WRITE_ACK:
                for j in range(len(self._packet_buffer)):
                    packet = self._packet_buffer[j]
                    if isinstance(packet, MemWriteAckPacket):     
                        if packet_processor.wait_for_memwrite_ack(packet):
                            packets_to_remove.add(j)
                            break
                continue

            if proc_stage == NTilePacketProc.SEND_ACK:
                packet_processor.send_ack_to_sys(self._tile_packet_interconnect)
                continue


        # Remove the packets that were processed.
        for packet_idx in packets_to_remove:
            self._packet_buffer.pop(packet_idx)

        # Remove the TilePacketProcessors that have completed.
        for packet_idx in processors_to_remove:
            self._tile_packet_processor_queue.pop(packet_idx)
             
        # Now, process all the PEs. 
        for i in range(self._num_pe_rows):
            for j in range(self._num_pe_cols):
                self._pe_grid[i][j].process()




    def _fetch_comm_packets(self):
        while (len(self._packet_buffer)) < self._packet_size:
            packet = self._interconnect.get_packet(self)
            if packet is None:
                return
            self._packet_buffer.append(packet)

    def _fetch_tile_packets(self):
        while(len(self._tile_packet_processor_queue)) < self._packet_size:
            packet = self._tile_packet_interconnect.get_packet(self)
            if packet is None:
                return
            self._tile_packet_processor_queue.append(NTilePacketProc(self._offchip_memory, packet))
