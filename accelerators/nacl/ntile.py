'''ntile.py

'''
from collections import OrderedDict

from accelerators.nacl.npe import NPE

from core.defines import Operator
from core.pe import PE
from core.tile import Tile
from core.message import *
from core.message_router import MessageRouter


class NTileMessageProc():
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

    def __init__(self, mem, tile_message):
        self._mem = mem
        self._tile_message = tile_message
        # First, grab the tile message ID
        self._tile_message_id = hex(id(self._tile_message))

        # Parse the first operand of the TilePacket
        source = self._tile_message.destination_device()
        #source, destination, message_id, seq_num, address
        self._read_req_op1 = MemoryReadRequest(source, self._mem, self._tile_message_id, 0, self._tile_message.op1_addr())
        self._read_req_op1_sent = False
        self._read_resp_op1 = None

        # Parse the second operand of the TilePacket
        self._read_req_op2 = MemoryReadRequest(source, self._mem, self._tile_message_id, 1, self._tile_message.op2_addr())
        self._read_req_op2_sent = False
        self._read_resp_op2 = None

        self._pe_message_sent = False
        self._pe_message_resp = None

        self._mem_write_message = None

        self._current_stage = self.SEND_READ
        self._next_stage = self.SEND_READ


    def update_stage(self):
        self._current_stage = self._next_stage      
        return self._current_stage



    def send_read_reqs(self, message_router):
        '''
        '''
        if self._current_stage != self.SEND_READ:
            return

        self._next_stage = self.SEND_READ
        if not self._read_req_op1_sent:
            self._read_req_op1_sent = message_router.send(self._read_req_op1)

        if not self._read_req_op2_sent:
            self._read_req_op2_sent = message_router.send(self._read_req_op2)

        if self._read_req_op1_sent and self._read_req_op2_sent:
            self._next_stage = self.WAIT_FOR_READ


    def listen_for_read_response(self,mem_ack_message):
        '''
        '''
        if self._current_stage != self.WAIT_FOR_READ:
            return False

        if self._tile_message_id == mem_ack_message.get_message_id():
            if mem_ack_message.get_seq_num() == 0:
                self._read_resp_op1 = mem_ack_message
                return True
            if mem_ack_message.get_seq_num() == 1:
                self._read_resp_op2 = mem_ack_message
                return True
        return False

    def handle_read_response(self):
        if self._current_stage != self.WAIT_FOR_READ:
            return

        self._next_stage = self.WAIT_FOR_READ

        if self._read_resp_op1 is not None and self._read_resp_op2 is not None:
            self._next_stage = self.DISPATCH

    def dispatch_to_PE(self, message_router, PE):
        if self._current_stage != self.DISPATCH:
            return False

        self._next_stage = self.DISPATCH

        if self._read_resp_op1 is None or self._read_resp_op2 is None:
            return False

        op1 = self._read_resp_op1.content()
        op2 = self._read_resp_op2.content()
        operation = self._tile_message.operation()
        source = self._tile_message.destination_device()
 
        PE_message = PECommand(source, PE, self._tile_message_id, 0, op1, op2, operation)
 
        if message_router.send(PE_message):
            self._pe_message_sent = True
            self._next_stage = self.WAIT_FOR_PE
            return True

        return False

    def listen_for_PE_response(self, PE_response_message):
        if self._current_stage != self.WAIT_FOR_PE:
            return False

        self._next_stage = self.WAIT_FOR_PE

        if PE_response_message.get_message_id() != self._tile_message_id:
            return False
        
        self._pe_message_resp = PE_response_message
        self._next_stage = self.WRITE_BACK
        return True

    def write_result(self, message_router):
        if self._current_stage != self.WRITE_BACK:
            return

        self._next_stage = self.WRITE_BACK

        res_addr = self._tile_message.res_addr()
        if message_router.send(MemoryWriteRequest(self._tile_message.destination_device(), self._mem, self._tile_message_id, 0, res_addr, self._pe_message_resp.result())):
            self._next_stage = self.WAIT_FOR_WRITE_ACK


    def wait_for_memwrite_ack(self, mem_write_ack_message):
        if self._current_stage != self.WAIT_FOR_WRITE_ACK:
            return False

        self._next_stage = self.WAIT_FOR_WRITE_ACK
        if mem_write_ack_message.get_message_id() == self._tile_message_id:
            self._next_stage = self.SEND_ACK
            return True

        return False



    def send_ack_to_sys(self, message_router):
        if self._current_stage != self.SEND_ACK:
            return 

        self._next_stage = self.SEND_ACK
        src = self._tile_message.destination_device()
        dst = self._tile_message.source_device()
        if message_router.send(TileCommandComplete(src, dst, self._tile_message.get_message_id())):
            self._next_stage = self.TERMINATE




class NTile(Tile): 

    def __init__(self, system_clock_ref, device_message_router, data_queue_size, tile_message_router, tile_message_queue_size, offchip_memory, num_pe_rows = 1, num_pe_cols = 1):
        Tile.__init__(self, system_clock_ref, device_message_router, data_queue_size)

        # Handling TilePacket Requests
        self._tile_message_processor_queue = list()
        self._tile_message_router = tile_message_router
        self._tile_message_router.add_connection(self)

        self._offchip_memory = offchip_memory
 

        # From the initialization parameters, 
        self._num_pe_rows = num_pe_rows
        self._num_pe_cols = num_pe_cols
        self._pe_grid = [[NPE(self._system_clock_ref, device_message_router)]*self._num_pe_cols for i in range(self._num_pe_rows)]

        # To handle more than 1 message at a time.
        self._message_buffer = list()
        self._message_size = tile_message_queue_size



    def process(self):


        self._fetch_tile_messages()
        self._fetch_comm_messages()

        messages_to_remove = set()
        processors_to_remove = set()


        for i in range(len(self._tile_message_processor_queue)):
            message_processor = self._tile_message_processor_queue[i]
            proc_stage = message_processor.update_stage()

            # Remove the processor.
            if proc_stage == NTileMessageProc.TERMINATE:
                processors_to_remove.add(i)
                continue

            if proc_stage == NTileMessageProc.SEND_READ:
                message_processor.send_read_reqs(self._message_router)
                continue

            if proc_stage == NTileMessageProc.WAIT_FOR_READ:  
                for j in range(len(self._message_buffer)):
                    message = self._message_buffer[j]
                    if isinstance(message, MemoryReadComplete):
                        if message_processor.listen_for_read_response(message):
                            messages_to_remove.add(j)
                message_processor.handle_read_response()
                continue

            if proc_stage == NTileMessageProc.DISPATCH:
                pe_hit = False            
                for i in range(self._num_pe_rows):
                    for j in range(self._num_pe_cols):
                        # get PE.
                        if message_processor.dispatch_to_PE(self._message_router, self._pe_grid[i][j]):
                            pe_hit = True 
                            break
                    if pe_hit:
                        break
                continue

            if proc_stage == NTileMessageProc.WAIT_FOR_PE:
                #listen_for_PE_response
                for j in range(len(self._message_buffer)):
                    message = self._message_buffer[j]
                    if isinstance(message, PEResponse):     
                        if message_processor.listen_for_PE_response(message):
                            messages_to_remove.add(j)
                            break
                continue

            if proc_stage == NTileMessageProc.WRITE_BACK:
                message_processor.write_result(self._message_router)
                continue

            if proc_stage == NTileMessageProc.WAIT_FOR_WRITE_ACK:
                for j in range(len(self._message_buffer)):
                    message = self._message_buffer[j]
                    if isinstance(message, MemoryWriteComplete):     
                        if message_processor.wait_for_memwrite_ack(message):
                            messages_to_remove.add(j)
                            break
                continue

            if proc_stage == NTileMessageProc.SEND_ACK:
                message_processor.send_ack_to_sys(self._tile_message_router)
                continue


        # Remove the messages that were processed.
        for message_idx in messages_to_remove:
            self._message_buffer.pop(message_idx)

        # Remove the TilePacketProcessors that have completed.
        for message_idx in processors_to_remove:
            self._tile_message_processor_queue.pop(message_idx)
             
        # Now, process all the PEs. 
        for i in range(self._num_pe_rows):
            for j in range(self._num_pe_cols):
                self._pe_grid[i][j].process()




    def _fetch_comm_messages(self):
        while (len(self._message_buffer)) < self._message_size:
            message = self._message_router.fetch(self)
            if message is None:
                return
            self._message_buffer.append(message)

    def _fetch_tile_messages(self):
        while(len(self._tile_message_processor_queue)) < self._message_size:
            message = self._tile_message_router.fetch(self)
            if message is None:
                return
            self._tile_message_processor_queue.append(NTileMessageProc(self._offchip_memory, message))
