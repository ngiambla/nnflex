''' nemem.py: A specialization of the memory class, for use with Nick's Accelerator

'''
from core.defines import Operator
from core.pe import PE 
from core.compackets import DataPacket, PERespPacket



class NPE(PE):

    EXE1 = 1
    EXE2 = 2
    DONE = 3
    RESP = 4
    WAIT = 5


    def __init__(self, system_clock_ref, interconnect):
        PE.__init__(self, system_clock_ref, interconnect, queue_size = 1)
        self._packet_to_process = None
        self._packet_to_send = None
        self._accumulator = 0
        self._pipeline_stage = self.WAIT
        self._next_stage = self.WAIT

    def process(self):
        # First, we must update out pipeline_stage
        self._pipeline_stage = self._next_stage

        # State Transitions

        # If we are in EXE1, move to EXE2
        if self._pipeline_stage == self.EXE1:
            self._next_stage = self.EXE2
            return

        # If we are in EXE2, move to DONE
        if self._pipeline_stage == self.EXE2:
            self._next_stage = self.DONE
            return

        # If we are in DONE, actually process the data, 
        # Two outcomes are possible:
        # 1. If Destination queue is full... try and SEND_AGAIN
        # 2. Otherwise, we can go back to waiting for a new packet to process!
        if self._pipeline_stage == self.DONE:
            # Currently, we are ONLY forming a PERespPacket
            op1 = self._packet_to_process.op1()
            op2 = self._packet_to_process.op2()
            dest = self._packet_to_process.source_device()
            packet_id = self._packet_to_process.get_packet_id()
            seq_num = self._packet_to_process.get_seq_num()

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

            self._packet_to_send = PERespPacket(self, dest, packet_id, seq_num, result)
            self._next_stage = self.RESP

        if self._pipeline_stage == self.RESP:
            self._next_stage = self.WAIT
            if not self._interconnect.send(self._packet_to_send):
                self._next_stage = self.RESP



        if self._pipeline_stage == self.WAIT:
            packet = self._interconnect.get_packet(self)
            if packet is None:
                self._next_stage = self.WAIT
                return

            self._packet_to_process = packet
            self._next_stage = self.EXE1
