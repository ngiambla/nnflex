''' squeeze.py:

Implement's the Squeeze ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Squeeze(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

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
        np.copyto(self._outputs[0], np.squeeze(self._inputs[0], self._inputs[1]))

        return tile_commands
