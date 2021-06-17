''' Nick G.'s Accelerator Example 

'''

from enum import Enum


from accelerators.nacl.nemem import NEMemory
from accelerators.nacl.ntile import NTile

from core.defines import Operator
from core.system import System
from core.message_router import MessageRouter
from core.message import TileCommand
from core.memory import MemoryMap


class NaClSupportLayer(Enum):
    CONV1D = 1
    CONV2D = 2
    LINEAR = 3
    ELEMWISEADD = 4

class NaCl(System):
    '''

    '''

    def __init__(self, num_tile_rows, num_tile_cols):
        System.__init__(self)


        self._layer_mapping = {
            "elemwiseadd": NaClSupportLayer.ELEMWISEADD,
            "linear" : NaClSupportLayer.LINEAR,
            "fc" : NaClSupportLayer.LINEAR,
            "gemv": NaClSupportLayer.LINEAR,
            "conv1d": NaClSupportLayer.CONV1D,
            "conv2d": NaClSupportLayer.CONV2D
        }

        # Define the interconnects that will be used to transfer data and control messages.
        #
        # Tile-ONLY MessageRouter:
        self._tile_message_router = MessageRouter(self._system_clock_ref)
        self._tile_message_router_queue_size = 2
        self._tile_message_router.add_connection(self, self._tile_message_router_queue_size)

        # MessageRouter for all devices.
        self._device_message_router = MessageRouter(self._system_clock_ref)
        self._device_message_router.add_connection(self)

        # Define the External Memory.
        self._memory = NEMemory(self._system_clock_ref, self._device_message_router, width=1e6)
        # When loading data (weight, activation, grad, etc)
        # into the memory, we can simply use a memory ptr
        self._memory_pointer = 0
        # And then, when we wish to refer to the original weight, activation, grad, etc,
        # we can query a memory map
        self._memory_map = dict()


        # Define the Number of Tiles we want.
        self._num_tile_rows = num_tile_rows
        self._num_tile_cols = num_tile_cols
        # Create the tiles.
        # NOTE: This architecture has PEs connecting 1 another.
        self._tiles = [[NTile(self._system_clock_ref, self._device_message_router, 2, self._tile_message_router, 2, self._memory, 1, 1)]*self._num_tile_cols for i in range(self._num_tile_rows)]


        # Define Tile Packet Vars.
        # For each Message we send to a tile, 
        # stamp it so it has an ID (we are going to track
        # responses from a tile.
        self._message_stamp = 0
        # Hold a list (queue) of tile commands to send
        self._tile_commands = list()
        # Hold onto a set representing required responses
        self._tile_required_resp = set()
        self._tile_resp_messages = list()


    def xfer_to_host(self, data):
        offset = self._memory_map[data]
        for i in range(len(data.data)):
            data.data[i] = self._memory._peek(offset+i)

    def xfer_from_host(self, data):
        self._memory_map[data] = self._memory_pointer
        for datum in data.data:
            self._memory._poke(self._memory_pointer, datum)
            self._memory_pointer += 1


    def forward(self, layer_type, input_acts, weights, output_acts):
        if layer_type.lower() not in self._layer_mapping:
            raise Exception("NaCl does not support the computation for this layer type: "+layer_type)

        self.xfer_from_host(input_acts)
        self.xfer_from_host(weights)
        self._memory_map[output_acts] = self._memory_pointer

        input_acts_offset = self._memory_map[input_acts]
        weights_offset = self._memory_map[weights]
        output_acts_offset = self._memory_map[output_acts]


        tile_row_idx = 0
        tile_col_idx = 0

        if self._layer_mapping[layer_type] == NaClSupportLayer.ELEMWISEADD:
            for i in range(len(input_acts.data)):
                op1_addr = input_acts_offset+i
                op2_addr = weights_offset+i
                res_addr = output_acts_offset+i
                operator = Operator.ADD
                dest = self._tiles[tile_row_idx][tile_col_idx]
                
                message_stamp = self._message_stamp                
                self._tile_commands.append(TileCommand(self, dest, message_stamp, op1_addr, op2_addr, res_addr, operator))
                self._message_stamp += 1


                
                tile_row_idx = (tile_row_idx+1) % self._num_tile_rows
                if tile_row_idx == 0:
                    tile_col_idx = (tile_col_idx+1) % self._num_tile_cols

        # for i in range(0, 100000):
        while self._tile_commands or self._tile_required_resp:
            self._fetch_tile_resp_messages()
            messages_to_remove = list()
            for i in range(len(self._tile_commands)):
                tile_message = self._tile_commands[i]
                if self._tile_message_router.send(tile_message):
                    self._tile_required_resp.add(tile_message.get_message_id())
                    messages_to_remove.append(i)

            for idx in messages_to_remove:
                self._tile_commands.pop(idx)

            self.process()

        self.xfer_to_host(output_acts)
        print("Total Number of Cycles: "+str(self._system_clock_ref.current_clock()))

        # If the memory was listed as external, this will
        self._memory.write_transaction_log()


    def process(self):
        '''
        '''
        self.tick()

        # Literally means to do an action in the clock cycle.
        self._memory.process()

        for i in range(self._num_tile_rows):
            for j in range(self._num_tile_cols):
                self._tiles[i][j].process()




    def _fetch_tile_resp_messages(self):
        messages_to_remove = list()

        while (len(self._tile_resp_messages)) < self._tile_message_router_queue_size:
            message = self._tile_message_router.fetch(self)
            if message is None:
                break
            self._tile_resp_messages.append(message)

        for i in range(len(self._tile_resp_messages)):
            message = self._tile_resp_messages[i]
            self._tile_required_resp.remove(message.get_message_id())
            messages_to_remove.append(i)

        for message_idx in messages_to_remove:
            self._tile_resp_messages.pop(message_idx)




