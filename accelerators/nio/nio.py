''' Nick G.'s Accelerator Example 

'''

from enum import Enum


from accelerators.nio.nio_mem import NioMemory
from accelerators.nio.nio_tile import NioTile

from core.defines import Operator
from core.system import System
from core.message_router import MessageRouter
from core.messaging import Message
from core.memory_map import MemoryMapper

from core.utils import *

class Nio(System):
    '''

    '''

    def __init__(self, num_tile_rows, num_tile_cols, memory_width = int(1e6)):
        System.__init__(self)


        # Tile-ONLY MessageRouter:
        self._tile_message_router = MessageRouter(self._system_clock_ref)
        self._tile_message_router_queue_size = 2
        self._tile_message_router.add_connection(self, self._tile_message_router_queue_size)

        # MessageRouter for all devices.
        self._device_message_router = MessageRouter(self._system_clock_ref)
        self._device_message_router.add_connection(self)

        # Define the External Memory.
        self._memory = NioMemory(self._system_clock_ref, self._device_message_router, width=memory_width)
        self._memory_mapper = MemoryMapper(self._memory, memory_width, 4)


        # Define the Number of Tiles we want.
        self._num_tile_rows = num_tile_rows
        self._num_tile_cols = num_tile_cols
        # Create the tiles.
        # NOTE: This architecture has PEs connecting 1 another.
        self._tiles = [[NioTile(self._system_clock_ref, self._device_message_router, 2, self._tile_message_router, self._memory, 4, 4)]*self._num_tile_cols for i in range(self._num_tile_rows)]

        self._tiles_flat = flatten(self._tiles)
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



    def forward(self, flexnode):
        '''
        '''
        flexnode.map(self._memory_mapper)
        flexnode.inputs2mem(self._memory_mapper)

        tile_row_idx = 0
        tile_col_idx = 0


                
        tile_row_idx = (tile_row_idx+1) % self._num_tile_rows
        if tile_row_idx == 0:
            tile_col_idx = (tile_col_idx+1) % self._num_tile_cols

        self._tile_commands = flexnode.compile(self, self._tiles_flat)

        while self._tile_commands or self._tile_required_resp:
            self._fetch_tile_resp_messages()
            
            sent_command_count = 0
            for i in range(len(self._tile_commands)):
                tile_message = self._tile_commands[i]

                if tile_message is None:
                    sent_command_count += 1
                    continue

                if self._tile_message_router.send(tile_message):       
                    self._tile_required_resp.add(tile_message.message_id)
                    self._tile_commands[i] = None

            self.process()

            if sent_command_count == (len(self._tile_commands)):
                self._tile_commands = list()

        flexnode.mem2output(self._memory_mapper)
        flexnode.unmap(self._memory_mapper)

        print("\nTotal Number of Cycles: "+str(self._system_clock_ref.current_clock()))

        # If the memory was listed as external, this will
        # self._memory.write_transaction_log()


    def process(self):
        '''
        '''
        self.tick()

        # Literally means to do an action in the clock cycle.
        self._memory.process()
        if self._system_clock_ref.current_clock() % 3 == 0:
            print("\rRunning: .  ", end="")
        if self._system_clock_ref.current_clock() % 3 == 1:
            print("\rRunning: .. ", end="")
        if self._system_clock_ref.current_clock() % 3 == 2:
            print("\rRunning: ...", end="")


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
            self._tile_required_resp.remove(message.message_id)
            messages_to_remove.append(i)

        for message_idx in messages_to_remove:
            self._tile_resp_messages.pop(message_idx)




