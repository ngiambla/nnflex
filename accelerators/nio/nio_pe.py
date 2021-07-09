''' nio_pe.py: A specialization of the PE class, for use with Nick's Accelerator

'''
from core.defines import Operator
from core.pe import PE 
from core.messaging import Message
from core.utils import *


class NioPE(PE):

    EXEC = 1
    DONE = 3
    RESP = 4
    WAIT = 5


    def __init__(self, system_clock_ref, message_router):
        PE.__init__(self, system_clock_ref, message_router)
        self._message_to_process = None
        self._message_to_send = None
        self._accumulator = 0
        self._pipeline_stage = self.WAIT
        self._next_stage = self.WAIT

    def process(self):
        # First, we must update out pipeline_stage
        self._pipeline_stage = self._next_stage

        # State Transitions

        # If we are in EXEC, move to DONE
        if self._pipeline_stage == self.EXEC:
            self._next_stage = self.DONE
            return

        # If we are in DONE, actually process the data, 
        # Two outcomes are possible:
        # 1. If Destination queue is full... try and SEND_AGAIN
        # 2. Otherwise, we can go back to waiting for a new message to process!
        if self._pipeline_stage == self.DONE:
            # Currently, we are ONLY forming a PEResponse message
            # print(self._message_to_process.operation)
            op1 = float_to_int_repr_of_float(self._message_to_process.op1)
            op2 = float_to_int_repr_of_float(self._message_to_process.op2)
            dest = self._message_to_process.source
            message_id = self._message_to_process.message_id
            seq_num = self._message_to_process.seq_num
            operator = self._message_to_process.operation
            result = 0

            if operator == Operator.ADD:
                result = op1+op2
            elif operator == Operator.SUB:
                result = op1-op2
            elif operator == Operator.MUL:
                result = op1*op2
            elif operator == Operator.DIV:
                result = op1/op2
            elif operator == Operator.MAC:
                self._accumulator += op1*op2
                result = self._accumulator
            elif operator == Operator.CLEAR:
                self._accumulator = 0
                result = self._accumulator
            elif operator == Operator.MAX:
                result = int(max(op1, op2))
            elif operator == Operator.MIN:
                result = int(min(op1, op2))

            attributes = {
                "result" : int_repr_of_float_to_float(result)
            }
            self._message_to_send = Message(self, dest, Message.PEDone, message_id, seq_num, attributes = attributes)
            self._next_stage = self.RESP

        if self._pipeline_stage == self.RESP:
            self._next_stage = self.WAIT
            if not self._message_router.send(self._message_to_send):
                self._next_stage = self.RESP



        if self._pipeline_stage == self.WAIT:
            message = self._message_router.fetch(self)
            if message is None:
                self._next_stage = self.WAIT
                return

            self._message_to_process = message
            self._next_stage = self.EXEC
