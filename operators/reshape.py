''' rely.py:

Implement's the ReLU ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Reshape(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

        in1 = self._inputs[0]
        in2 = self._inputs[1]
        out = self._outputs[0]


        self._in1_offset = 0
        self._out_offset = 0



    def map(self, memory_mapper):
        pass

    def unmap(self, memory_mapper):
        pass

    def _inputs2mem(self, memory_xfer_engine):
        pass

    def _mem2output(self, memory_xfer_engine):
        pass

    def compile(self, source, destinations):
        '''
        '''

        tile_commands = list()

        self._outputs[0] = self._inputs[0].reshape(tuple(self._inputs[1]))

        return tile_commands
