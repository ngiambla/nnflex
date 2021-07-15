''' Nick G.'s Accelerator Example 

'''
import time

from enum import Enum

# Example of a Non-Pipelined Memory
#from accelerators.nio.nio_mem import NioMemory

# Example of a Pipelined Memory.
from accelerators.nio.nio_mem_piped import NioMemory
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

    def __init__(self, num_tile_rows, num_tile_cols, memory_width = int(1e8)):
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
        self._tiles = [[NioTile(self._system_clock_ref, self._device_message_router, 2, self._tile_message_router, self._memory, 1, 1)]*self._num_tile_cols for i in range(self._num_tile_rows)]

        self._tiles_flat = flatten(self._tiles)
        # Define Tile Packet Variables:
        # 1. Hold a list (queue) of tile commands to send
        self._tile_commands = list()
        # 2. Hold onto a set representing required responses
        self._tile_required_resp = set()
        self._tile_resp_messages = list()
  
        # Tracks the last cycles required per layer.
        self._cycles_per_layer = 0
        # Hold onto the name of the layer we are processing (only needed for CLI)
        self._current_layer_name = ""

        self._layer_progress = 0
        self._tile_cmds_per_layer = 0
        self._real_start = None



    def forward(self, flexnode):
        ''' forward:

        Conducts the forward pass for the provided flexnode and this architecture.

        '''
        # Capture the name of the layer we are processing (only for UI)
        self._current_layer_name = flexnode.get_op_name()
        # Record the cycle-count prior to the forward pass
        self._cycles_per_layer = self._system_clock_ref.current_clock()

        # Record the actual time (identify the simulator's cycles/sec)
        start_time = time.time()
        if self._real_start is None:
            self._real_start = start_time

        # Map the node's input and outputs to memory.
        flexnode.map(self._memory_mapper)
        print("Compiling Layer ["+flexnode.get_op_name()+"]")

        self._tile_commands = flexnode.compile(self, self._tiles_flat)   


        # Set the layer progress.
        self._tile_cmds_per_layer = len(self._tile_commands)
        if self._tile_cmds_per_layer == 0:
            self._tile_cmds_per_layer = 1
            self._layer_progress = 1
            self.progress()

        self._layer_progress = 0

        i = 0
        sent_command_count = 0

        while self._tile_commands or self._tile_required_resp:
            self._fetch_tile_resp_messages()

            while i < len(self._tile_commands) and self._tile_message_router.send(self._tile_commands[i]):
                self._tile_required_resp.add(self._tile_commands[i].message_id)
                self._tile_commands[i] = None
                i += 1
                sent_command_count += 1

            self.progress()
            self.process()

            if sent_command_count == (len(self._tile_commands)):
                self._tile_commands = list()


        flexnode.unmap(self._memory_mapper)
        end_time = time.time()

        # Clear the cache after every layer.
        for i in range(self._num_tile_rows):
            for j in range(self._num_tile_cols):
                self._tiles[i][j].evict_cache_lines()        

        self._cycles_per_layer = self._system_clock_ref.current_clock() - self._cycles_per_layer
        print("\nCycles For Layer ["+flexnode.get_op_name()+"]: " + str(self._cycles_per_layer))
        print("Stalled Cycles: "+str(self.number_of_stalled_cycles()))
        print("Total Number of Cycles: " + str(self._system_clock_ref.current_clock()))
        print("Simulator Performance Per Layer: "+"{:10.2f} cycles/sec".format(self._cycles_per_layer/(end_time-start_time)))

        # If the memory was listed as external, this will
        self._memory.write_transaction_log()

    def progress(self):
        # Define local variable.
        bar_size = 25

        # Display a progress bar for the user.
        progress_header = "\r[" + self._current_layer_name + "] Running: "
        progress = " "*bar_size
        dot_index = self._system_clock_ref.current_clock() % bar_size
        progress = progress[:dot_index] + "." + progress[dot_index+1:]
        percentage = " {:5.2f}% Complete".format(100*self._layer_progress/self._tile_cmds_per_layer)
        fraction = " [{:10d}/{:10d}]".format(self._layer_progress, self._tile_cmds_per_layer) 
        print(progress_header+progress+percentage+fraction, end = "")


    def process(self):
        ''' process:

        For the current clock cycle, process all state changes and required updates for the
        entire system (System -> Memory -> Tiles -> PEs)
        '''
        self.tick()

        # Process the memory for this clock cycle.
        self._memory.process()
        
        # For each tile, process their states in this clock cycle.
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
            self._layer_progress += 1
            messages_to_remove.append(i)

        reversed_messages = messages_to_remove
        reversed_messages.reverse()
        for message_idx in reversed_messages:
            self._tile_resp_messages.pop(message_idx)



    def number_of_stalled_cycles(self):
        num_stalls = 0
        for i in range(self._num_tile_rows):
            for j in range(self._num_tile_cols):
                num_stalls += self._tiles[i][j].number_of_stalled_cycles()
        return num_stalls + self._memory.number_of_stalled_cycles()
