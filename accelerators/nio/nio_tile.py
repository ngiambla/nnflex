'''ntile.py

'''
import uuid

from collections import OrderedDict

# from accelerators.nio.nio_pe import NioPE
from accelerators.nio.nio_piped_pe import NioPE

from core.defines import Operator
from core.pe import PE
from core.tile import Tile
from core.messaging import Message
from core.message_router import MessageRouter
from core.cache import Cache

from core.utils import *

class NioTile(Tile):
    IDLE = 0
    SEND_READS = 1
    WAIT_FOR_READS = 2
    DISPATCH_TO_PE = 3
    WAIT_FOR_PE = 4
    WRITE_BACK = 5
    WAIT_FOR_WRITE_ACK = 6
    SEND_ACK = 7
    FETCH = 9

    def __init__(self, system_clock_ref, device_message_router, data_queue_size, tile_message_router, offchip_memory, num_pe_rows = 1, num_pe_cols = 1):
        Tile.__init__(self, system_clock_ref, device_message_router, data_queue_size)

        # Handling TilePacket Requests
        self._tile_message_processor_queue = list()
        self._tile_message_router = tile_message_router
        self._tile_message_router.add_connection(self)
        self._offchip_memory = offchip_memory
 
        # From the initialization parameters, 
        self._num_pe_rows = num_pe_rows
        self._num_pe_cols = num_pe_cols
        self._pe_grid = [[NioPE(self._system_clock_ref, device_message_router)]*self._num_pe_cols for i in range(self._num_pe_rows)]

        # Only process 1 tile at a time. 
        self._tile_message = None
        self._device_message = None

        # Handle Bias Carefully:
        self._bias_map = dict()

        # For read and writes to memory.
        self._reads_to_send = list()
        self._read_responses = dict()

        self._dispatch_queue = list()
        self._dispatch_queue_ack = dict()

        self._writes_to_send = list()
        self._writes_responses = dict()

        self._tile_ack = None

        self._current_stage = self.IDLE
        self._next_stage = self.IDLE

        self._cache = Cache(10000)


    def load_cache(self, address_list):
        for addr in address_list:
            self._cache.install(addr, self._memory_system_peek(addr))

    def evict_cache_lines(self):
        self._cache.clear()

    def process(self):


        self._fetch_comm_messages()


        for i in range(self._num_pe_rows):
            for j in range(self._num_pe_cols):
                self._pe_grid[i][j].process()    

        self._current_stage = self._next_stage

        if self._current_stage == self.FETCH:
            msg = self._tile_message
            op = msg.operation
            if op in {Operator.ADD, Operator.MUL, Operator.SUB, Operator.DIV, Operator.MAX}:
                # Two operations require for the operators..
                op1_addr = None
                op2_addr = None

                if not hasattr(msg, "op1"):
                    attributes = {
                        "addr" : int(msg.op1_addr)
                    }
                    msg_stamp = uuid.uuid4()
                    self._reads_to_send.append(Message(self, self._offchip_memory, Message.MemRead, msg_stamp, 1, attributes=attributes))
                    self._read_responses[str(msg_stamp)+str(1)] = None
                else:
                    self._read_responses["1"] = msg.op1

                if not hasattr(msg, "op2"):
                    attributes = {
                        "addr" : int(msg.op2_addr)
                    }                    
                    msg_stamp = uuid.uuid4()
                    self._reads_to_send.append(Message(self, self._offchip_memory, Message.MemRead, msg_stamp, 2, attributes=attributes))
                    self._read_responses[str(msg_stamp)+str(2)] = None
                else:
                    self._read_responses["2"] = msg.op2

            elif op in {Operator.DOT}:
                for data_row in [msg.col_addrs, msg.row_addrs]:
                    idx = 0
                    msg_stamp = uuid.uuid4()
                    for addr in data_row:
                        contents = self._cache.lookup(addr)
                        if contents is None:
                            attributes = {
                                "addr" : int(addr)
                            }   
                            self._reads_to_send.append(Message(self, self._offchip_memory, Message.MemRead, msg_stamp, idx, attributes=attributes))
                            self._read_responses[str(msg_stamp)+str(idx)] = None
                        else:
                            self._read_responses[str(msg_stamp)+str(idx)] = contents
                        idx+=1

                    if self._cache.lookup(msg.res_addr) is not None:
                        raise ValueError("Cache will fail.")


                if msg.bias is not None:
                    contents = self._cache.lookup(msg.bias)
                    if contents is None:                    
                        attributes = {
                            "addr" : int(msg.bias)
                        }   
                        msg_stamp = uuid.uuid4()                
                        self._reads_to_send.append(Message(self, self._offchip_memory, Message.MemRead, msg_stamp, idx, attributes=attributes))
                        self._read_responses[str(msg_stamp)+str(idx)] = None
                    else:
                        self._read_responses[str(msg_stamp)+str(idx)] = contents

            else:
                raise ValueError("Unhandled operation during FETCH.")

            self._next_stage = self.SEND_READS


        if self._current_stage == self.SEND_READS:
            self._next_stage = self.SEND_READS
            if self._reads_to_send:
                message = self._reads_to_send[0]
                if self._message_router.send(message):
                    self._reads_to_send.pop(0)


            if self._device_message is not None:
                read_id = str(self._device_message.message_id) + str(self._device_message.seq_num)
                if read_id not in self._read_responses:
                    raise ValueError("Memory Read Response Mismatch. Received Message: "+read_id)
                self._read_responses[read_id] = self._device_message.content
                self._cache.install(self._device_message.addr, self._device_message.content)
                self._device_message = None

            if not self._reads_to_send and None not in self._read_responses.values():
                self._next_stage = self.DISPATCH_TO_PE

                msg = self._tile_message
                op = msg.operation


                if op in {Operator.ADD, Operator.MUL, Operator.SUB, Operator.DIV, Operator.MAX}:

                    msg_stamp = uuid.uuid4()  
                    attributes = {
                        "operation" : op,
                        "dtype" : msg.dtype
                        }
                    idx = 1
                    for readout in self._read_responses.values():
                        attributes["op"+str(idx)] = readout
                        idx += 1
                    self._dispatch_queue.append(Message(self, self._pe_grid[0][0], Message.PECmd, msg_stamp, attributes=attributes))                


                elif op in {Operator.DOT}:              

                    values = list(self._read_responses.values())
                    for i in range(len(msg.col_addrs)):
                        msg_stamp = uuid.uuid4() 
                        attributes = {
                            "operation" : Operator.CMAC if i == 0 else Operator.MAC,
                            "dtype" : msg.dtype,
                            "op1" : values[i],
                            "op2" : values[i+len(msg.col_addrs)]
                            }
                        self._dispatch_queue.append(Message(self, self._pe_grid[0][0], Message.PECmd, msg_stamp, attributes=attributes))

        
                    if msg.bias is not None:
                        msg_stamp = uuid.uuid4()
                        attributes = {
                            "operation" : Operator.MAC,
                            "dtype" : msg.dtype,
                            "op1" : values[-1],
                            "op2" : float_to_int_repr_of_float(1)
                            }
                        self._dispatch_queue.append(Message(self, self._pe_grid[0][0], Message.PECmd, msg_stamp, attributes=attributes))
                else:
                    raise NotImplementedError("Unhandled operation: "+str(op))

        if self._current_stage == self.DISPATCH_TO_PE:
            self._next_stage = self.DISPATCH_TO_PE
            if self._dispatch_queue:
                message = self._dispatch_queue[0]
                if self._message_router.send(message):
                    self._dispatch_queue_ack[str(message.message_id)+str(message.seq_num)] = None
                    self._dispatch_queue.pop(0)

            last_message = None

            if self._device_message is not None:
                read_id = str(self._device_message.message_id) + str(self._device_message.seq_num)
                if read_id not in self._dispatch_queue_ack:
                    raise ValueError("PE Response Mismatch. Received Message: "+read_id)
                self._dispatch_queue_ack[read_id] = [self._device_message.result, self._device_message.seq_num]
                last_message = self._device_message
                self._device_message = None    


            if not self._dispatch_queue and None not in self._dispatch_queue_ack.values():
                self._next_stage = self.WRITE_BACK
                attributes = {
                    "dtype" : self._tile_message.dtype,
                    "content" : float_to_int_repr_of_float(last_message.result),
                    "addr" : int(self._tile_message.res_addr)
                    }
                msg_stamp = uuid.uuid4()                    
                self._writes_to_send.append(Message(self, self._offchip_memory, Message.MemWrite, msg_stamp, attributes=attributes))                

        if self._current_stage == self.WRITE_BACK:            
            self._next_stage = self.WRITE_BACK
            if self._writes_to_send:
                message = self._writes_to_send[0]
                if self._message_router.send(message):
                    self._writes_responses[str(message.message_id)+str(message.seq_num)] = None
                    self._writes_to_send.pop(0)

            if self._device_message is not None:
                read_id = str(self._device_message.message_id) + str(self._device_message.seq_num)
                if read_id not in self._writes_responses:
                    raise ValueError("Memory Write Response Mismatch. Received Message: "+read_id)
                self._writes_responses[read_id] = True
                self._device_message = None

            if None not in self._writes_responses.values() and not self._writes_to_send:
                self._next_stage = self.SEND_ACK
                self._tile_ack = Message(self, self._tile_message.source , Message.TileDone, self._tile_message.message_id)

        if self._current_stage == self.SEND_ACK:
            self._next_stage = self.SEND_ACK
            if self._tile_message_router.send(self._tile_ack):
                self._current_stage = self.IDLE

        if self._current_stage == self.IDLE:
            # Clear out state from last transaction.            
            self._read_responses = dict()
            self._dispatch_queue_ack = dict()
            self._writes_responses = dict()
            self._tile_ack = None

            # Fetch a tile-packet.
            if not self._fetch_tile_messages():
                self._next_stage = self.IDLE
                return
            # Otherwise, continue on to the next stage.
            self._next_stage = self.FETCH

    def _fetch_comm_messages(self):
        if self._device_message is not None:
            return
        message = self._message_router.fetch(self)
        if message is None:
            return
        self._device_message = message

    def _fetch_tile_messages(self):
        if self._current_stage is not self.IDLE:
            return False
        message = self._tile_message_router.fetch(self)
        if message is None:
            return False
        self._tile_message = message
        return True


    def number_of_stalled_cycles(self):
        stalls = 0
        for i in range(self._num_pe_rows):
            for j in range(self._num_pe_cols):
                stalls += self._pe_grid[i][j].number_of_stalled_cycles()    
        return stalls + self._num_stalls
