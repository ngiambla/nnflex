from core.defines import Operator
from core.pe import PE
from core.tile import Tile

from core.compackets import DataPacket, PEPacket
from core.interconnect import Interconnect

class NTileStage(Enum):
    # Wait for Packets on Interconnect
    WAIT = 0
    DISPATCH = 0


class NTile(Tile): 

    def __init__(self, system_clock_ref, external_interconnect, offchip_memory, num_pe_rows = 1, num_pe_cols = 1):
        Tile.__init__(system_clock_ref, external_interconnect)

        self._offchip_memory = offchip_memory
 
        # Create a local interconnect.
        self._local_interconnect = Interconnect(self._system_clock_ref)

        # Create a local memory to buffer data.
        self._local_memory = Memory()

        # Add the memories to the local interconnect
        self._local_interconnect.add(self._local_memory)

        # From the initialization parameters, 
        self._num_pe_rows = num_pe_rows
        self._num_pe_cols = num_pe_cols
        self._pe_grid = [[NPE(self._system_clock_ref, self._local_interconnect, self)]*self._num_pe_cols for i in range(self._num_pe_rows)]

        # To handle more than 1 packet at a time.
        self._packet_buffer = list()
        self._packet_size = 2

        # Our State Change Handlers
        self._pipeline_stage = NTileStage.WAIT
        self._next_stage = NTileStage.WAIT


    def process(self):

        # # First, we must update our pipeline_stage
        # self._pipeline_stage = self._next_stage

        # # State Transitions
        # if self._pipeline_stage == NTileStage.WAIT:

        #     self.load_packets_from_interconnect()

        #     if not self._packet_to_process:
        #         self._next_stage = NTileStage.WAIT
        #         return

        #     self._next_stage = NTileStage.DISPATCH

        self._load_packets_from_interconnect()
        for packet in self._packet_buffer:
            if isinstance(packet, MemReadPacket):
                


        for i in range(self._num_pe_rows):
            for j in range(self._num_pe_cols):
                self._pe_grid[i][j].process()




    def _load_packets_from_interconnect(self):
        while len(self._packet_buffer) < self._packet_size:
            packet = self._interconnect.get_packet(self)
            if not packet:
                return
            self._packet_buffer.append(packet)
