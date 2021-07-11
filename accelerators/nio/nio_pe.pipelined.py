''' nio_pe.py: A specialization of the PE class, for use with Nick's Accelerator

'''
from core.defines import Operator
from core.pe import PE
from core.pipeline import Stage
from core.messaging import Message
from core.utils import *


class NioPE(PE):

    def __init__(self, system_clock_ref, message_router):
        PE.__init__(self, system_clock_ref, message_router)
        self._pipeline = [None for x in range(0,3)]
        self._pipeline[0] = IdleStage(self, self._message_router)
        self._pipeline[1] = ExecStage(self)
        self._pipeline[2] = AcknStage(self, self._message_router)
        self._stall = False
        self._num_stalls = 0
    def process(self):
        # If we are stalled, only process a send...
        if self._stall:
            self.pipeline[-1].process()
            return
        # Otherwise, proceed with processing.
        self._pipeline[2].accept_message(self._pipeline[1].get_message())
        self._pipeline[1].accept_message(self._pipeline[0].get_message())

        for stage in self._pipeline:
            stage.process()

    def stall(self):
        self._stall = True

    def continue_processing(self):
        self._stall = False

    
class IdleStage(Stage):
    def __init__(self, nio_pe, router):
        Stage.__init__(self)
        self._nio_pe = nio_pe
        self._router = router

    def process(self):
        self._message = self._router.fetch(self._nio_pe)


class ExecStage(Stage):
    def __init__(self, nio_pe):
        Stage.__init__(self)
        self._accumulator = 0
        self._nio_pe = nio_pe

    def process(self):
        if self._message is None:
            return

        op1 = int_repr_of_float_to_float(self._message.op1)
        op2 = int_repr_of_float_to_float(self._message.op2)
        dest = self._message.source
        message_id = self._message.message_id
        seq_num = self._message.seq_num
        operator = self._message.operation
        result = 0

        if operator == Operator.ADD:
            result = op1+op2
        elif operator == Operator.SUB:
            result = op1-op2
        elif operator == Operator.MUL:
            result = op1*op2
        elif operator == Operator.DIV:
            result = op1/op2
        elif operator == Operator.CMAC:
            self._accumulator = op1*op2
            result = self._accumulator
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
            "result" : float_to_int_repr_of_float(result)
        }
        self._message = Message(self._nio_pe, dest, Message.PEDone, message_id, seq_num, attributes = attributes)

class AcknStage(Stage):
    def __init__(self, nio_pe, router):
        Stage.__init__(self)
        self._nio_pe = nio_pe
        self._router = router

    def process(self):
        if self._message is None:
            return
        if not self._router.send(self._message):
            self._nio_pe.stall()
        else:
            self._nio_pe.continue_processing()
