''' matmul.py:

Implement's the MatMul ONNX node as a flexnode (for use with any accelerator)

'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class MatMul(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)


        self._in1_shape = None
        self._in1_flat = None

        self._in2_shape = None
        self._in2_flat = None 
        
        self._out_shape = None
        self._out_flat =  None        

        self._in1_offset = 0
        self._in2_offset = 0 
        self._out_offset = 0



    def map(self, memory_mapper):
        
        in1 = self._inputs[0]
        self._in1_shape = in1.shape
        self._in1_flat = in1.flatten()

        in2 = self._inputs[1]
        self._in2_shape = in2.shape
        self._in2_flat = in2.flatten()
        
        out = self._outputs[0]
        self._out_shape = out.shape
        self._out_flat = out.flatten()

        self._in1_offset = memory_mapper.map(self._in1_flat)
        self._in2_offset = memory_mapper.map(self._in2_flat)
        self._out_offset = memory_mapper.map(self._out_flat)

        self._inputs2mem(memory_mapper)

    def unmap(self, memory_mapper):
        self._mem2output(memory_mapper)
        memory_mapper.unmap(self._in1_flat)
        memory_mapper.unmap(self._in2_flat)
        memory_mapper.unmap(self._out_flat)

    def _inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._in1_flat, self._in1_offset)
        memory_xfer_engine.sys2mem(self._in2_flat, self._in2_offset)

    def _mem2output(self, memory_xfer_engine):
        memory_xfer_engine.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._out_shape)
            self._outputs[0][multi_index] = self._out_flat[i]

    def compile(self, source, destinations):
        '''
        '''

        tile_commands = list()
        out_shape = self._out_shape
        in1_shape = self._in1_shape
        in2_shape = self._in2_shape

        in1_rows = in1_shape[0]
        in2_rows = in2_shape[0]
        in2_cols = in2_shape[1]

        num_destinations = len(destinations)
        which_dest = 0

        seen_output = set()

        for i in range(in1_rows):
            for j in range(in2_cols):
                row_addrs = list()
                col_addrs = list()
                out_idx = self.ravel_multi_index([i,j], out_shape) + self._out_offset

                if out_idx not in seen_output:
                    seen_output.add(out_idx)
                else:
                    raise ValueError("Seen this output before: "+str(seen_output))                

                destination = destinations[which_dest]

                for k in range(in2_rows):
                    row_addrs.append(self.ravel_multi_index([i,k], in1_shape) + self._in1_offset)
                    col_addrs.append(self.ravel_multi_index([k,j], in2_shape) + self._in2_offset)

                attributes = {
                    "res_addr" : out_idx,
                    "operation" : Operator.DOT,
                    "dtype" : self._out_flat.dtype,
                    "col_addrs" : col_addrs,
                    "row_addrs" : row_addrs,
                }

                message_stamp = uuid.uuid4()
                tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                tile_commands.append(tile_command)
                which_dest += 1
                which_dest = which_dest % num_destinations

        return tile_commands
