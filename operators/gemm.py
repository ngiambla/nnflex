''' gemm.py:

Implement's the GeMM ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class GeMM(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

        self._alpha = 1.0
        self._beta = 1.0
        self._transA = 0
        self._transB = 0

        self.fill_attributes(onnx_node)

        in1 = self._inputs[0] if self._transA == 0 else np.transpose(self._inputs[0])
        in1 *= self._alpha
        self._in1_shape = in1.shape
        self._in1_flat = in1.flatten()

        in2 = self._inputs[1] if self._transB == 0 else np.transpose(self._inputs[1])
        self._in2_shape = in2.shape
        self._in2_flat = in2.flatten()
        

        out = self._outputs[0]
        self._out_shape = out.shape
        self._out_flat = out.flatten()

        in3 = None
        self._in3_flat = None
        if len(self._inputs) == 3:
            in3 = self._beta * np.broadcast_to(self._inputs[2], self._out_shape)
            self._in3_shape = in3.shape
            self._in3_flat = in3.flatten()

        self._in1_offset = 0
        self._in2_offset = 0 
        self._in3_offset = 0
        self._out_offset = 0


    def fill_attributes(self, onnx_node):
        for attr in onnx_node.attribute:
            if attr.name == "alpha":
                self._alpha = float(attr.f)
            if attr.name == "beta":
                self._beta = float(attr.f)
            if attr.name == "transA":
                self._transA = int(attr.i)
            if attr.name == "transB":
                self._transB = int(attr.i)



    def map(self, memory_mapper):
        self._in1_offset = memory_mapper.map(self._in1_flat)
        self._in2_offset = memory_mapper.map(self._in2_flat)
        self._out_offset = memory_mapper.map(self._out_flat)
        if self._in3_flat is not None:
            self._in3_offset = memory_mapper.map(self._in3_flat)

    def unmap(self, memory_mapper):
        memory_mapper.unmap(self._in1_flat)
        memory_mapper.unmap(self._in2_flat)
        memory_mapper.unmap(self._out_flat)
        if self._in3_flat is not None:
            memory_mapper.unmap(self._in3_flat)

    def inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._in1_flat, self._in1_offset)
        memory_xfer_engine.sys2mem(self._in2_flat, self._in2_offset)
        if self._in3_flat is not None:
            memory_xfer_engine.sys2mem(self._in3_flat, self._in3_offset)

    def mem2output(self, memory_xfer_engine):
        memory_xfer_engine.transfer_to_memory.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._out_shape)
            self._outputs[0][multi_index] = self._out_flat[i]

    def compile(self, source, destination):
        '''
        '''

        tile_commands = list()
        out_shape = self._out_shape
        in1_shape = self._in1_shape
        in2_shape = self._in2_shape

        in1_rows = in1_shape[0]
        in2_rows = in2_shape[0]
        in2_cols = in2_shape[1]

        for i in range(in1_rows):
            for j in range(in2_cols):
                row_addrs = list()
                col_addrs = list()
                print(i, j)
                out_idx = self.ravel_multi_index([i,j], out_shape) + self._out_offset

                for k in range(in2_rows):
                    row_addrs.append(self.ravel_multi_index([i,k], in1_shape)+self._in1_offset)
                    col_addrs.append(self.ravel_multi_index([k,j], in2_shape)+self._in2_offset)

                attributes = {
                    "res_addr" : out_idx,
                    "operation" : Operator.DOT,
                    "dtype" : self._out_flat.dtype,
                    "col_addrs" : col_addrs,
                    "row_addrs" : row_addrs,
                }

                if self._in3_flat is not None:
                    attributes["bias"] = self.ravel_multi_index([i,j], out_shape) + self._in3_offset

                message_stamp = uuid.uuid4()
                tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                tile_commands.append(tile_command)

        return tile_commands
