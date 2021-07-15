''' transpose.py:

Implement's the Transpose ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Transpose(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)
        self._axes = None
        self.fill_attributes(onnx_node)

    def fill_attributes(self, onnx_node):
        for attr in onnx_node.attribute:
            if attr.name == "perm":
                self._axes = attr.ints


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
        np.copyto(self._outputs[0], np.transpose(self._inputs[0], self._axes))
        return tile_commands
