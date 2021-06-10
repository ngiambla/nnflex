from core.defines import Operator
from core.pe import PE 
from core.compackets import DataPacket, PEPacket


class NPEStage(Enum):
    EXE1 = 1
    EXE2 = 2
    DONE = 3
    WAIT = 4
    SEND_AGAIN = 5

class NPE(PE):
    def __init__(self, system_clock_ref, interconnect, destination):
        PE.__init__(system_clock_ref, interconnect, queue_size = 1)
        self._packet_to_process = None
        self._packet_to_send = None
        self._accumulator = 0
        self._pipeline_stage = NPEStage.WAIT
        self._next_stage = NPEStage.WAIT
        self._destination = _destination

    def process(self):
        # First, we must update out pipeline_stage
        self._pipeline_stage = self._next_stage

        # State Transitions

        # If we are in EXE1, move to EXE2
        if self._pipeline_stage == NPEStage.EXE1:
            self._next_stage = NPEStage.EXE2
            return

        # If we are in EXE2, move to DONE
        if self._pipeline_stage == NPEStage.EXE2:
            self._next_stage = NPEStage.DONE
            return

        # If we are in DONE, actually process the data, 
        # Two outcomes are possible:
        # 1. If Destination queue is full... try and SEND_AGAIN
        # 2. Otherwise, we can go back to waiting for a new packet to process!
        if self._pipeline_stage == NPEStage.DONE:
            # Currently, we are ONLY forming a datapacket,
            # however, we could hook the PE directly into a memory dev.
            op1 = self._packet_to_process.op1()
            op2 = self._packet_to_process.op2()
            operator = self._packet_to_process.operation()
            result = 0

            if operator == Operator.ADD:
                result = op1+op2
            elif operator == Operator.SUB:
                result = op1-op2
            elif operator == Operator.MULT:
                result = op1*op2
            elif operator == Operator.DIV:
                result = op1/op2
            elif operator == Operator.MAC:
                self._accumulator += op1*op2
                result = self._accumulator
            elif operator == Operator.CLEAR:
                self._accumulator = 0
                result = self._accumulator

            self._packet_to_send = DataPacket(self, self._destination, result)
            if not self._interconnect.send(self._packet_to_send):
                self._next_stage = NPEStage.SEND_AGAIN
            else:
                self._next_stage = NPEStage.WAIT

        if self._pipeline_stage == NPEStage.SEND_AGAIN:
            if not self._interconnect.send(self._packet_to_send):
                self._next_stage = NPEStage.SEND_AGAIN
            else:
                self._next_stage = NPEStage.WAIT


        if self._pipeline_stage == NPEStage.WAIT:
            packet = self._interconnect.get_packet(self)
            if packet is None:
                self._next_stage = NPEStage.WAIT
                return

            self._packet_to_process = packet
            self._next_stage = NPEStage.EXE1


    def set_destination(self, new_destination):
        # NOTE: this is for f l e x i b l e architectures.
        # use with caution. 
        self._destination = new_destination
