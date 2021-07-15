''' clip.py:

Implement's the clip ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Clip(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)
        self._min = -3.402823466e+38
        self._max = 3.402823466e+38

        if len(inputs) != 1 and len(inputs) != 3:
            raise ValueError("Clip can only have 1 or 3 inputs.")

        self._input = inputs[0]

        if len(inputs) == 3:
            self._min = inputs[1]
            self._max = inputs[2]        

    def map(self, memory_mapper):
        pass

    def unmap(self, memory_mapper):
        pass

    def _inputs2mem(self, memory_xfer_engine):
        pass

    def _mem2output(self, memory_xfer_engine):
        pass

    def compile(self, source, destinations):

        tile_commands = list()

        # Here, we are NOT generating tile_commands, (although, this is not difficult.)
        np.copyto(self._outputs[0], np.clip(self._input, self._min, self._max))

        return tile_commands
