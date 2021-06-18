''' rely.py:

Implement's the ReLU ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class ReLU(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

        in1 = self._inputs[0]
        out = self._outputs[0]

        self._in1_flat = in1.flatten()
        self._out_flat = out.flatten()

        self._length = len(self._in1_flat)

        self._in1_offset = 0
        self._out_offset = 0

        self._operation = Operator.MAX



    def map(self, memory_mapper):
        self._in1_offset = memory_mapper.map(self._in1_flat)
        self._in2_offset = memory_mapper.map(self._in2_flat)
        self._out_offset = memory_mapper.map(self._out_flat)

    def unmap(self, memory_mapper):
        memory_mapper.unmap(self._in1_flat)
        memory_mapper.unmap(self._in2_flat)
        memory_mapper.unmap(self._out_flat)

    def inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._in1_flat, self._in1_offset)
        memory_xfer_engine.sys2mem(self._in2_flat, self._in2_offset)

    def mem2output(self, memory_xfer_engine):
        memory_xfer_engine.transfer_to_memory.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._outputs[0].shape)
            self._outputs[0][multi_index] = self._out_flat[i]

    def compile(self, source, destination):
        '''
        '''

        tile_commands = list()

        for i in range(self._length):
            op1_addr = self._in1_offset+i
            res_addr = self._out_offset+i

            attributes = {
                "op1_addr" : op1_addr,
                "op2" : 0,
                "res_addr" : res_addr,
                "operation" : self._operation,
                "dtype" : self._out_flat.dtype
            }

            message_stamp = uuid.uuid4()
            tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
            tile_commands.append(tile_command)

        return tile_commands
