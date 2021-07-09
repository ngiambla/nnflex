''' conv.py:

Implement's the conv ONNX node as a flexnode (for use with any accelerator)

'''
import itertools
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Conv(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

        self._autopad = "NOTSET"
        self._dilations = None
        self._group = 1
        self._kernel_shape = None
        self._pads = None
        self._strides = None

        self.fill_attributes(onnx_node)

        in1 = self._inputs[0]
        self._in1_shape = in1.shape
        self._in1_flat = in1.flatten()

        in2 = self._inputs[1]
        self._in2_shape = in2.shape
        self._in2_flat = in2.flatten()
        

        out = self._outputs[0]
        self._out_shape = out.shape
        self._out_flat = out.flatten()

        in3 = None
        self._in3_flat = None
        if len(self._inputs) == 3:
            in3 = np.broadcast_to(self._inputs[2], self._out_shape)
            self._in3_shape = in3.shape
            self._in3_flat = in3.flatten()

        self._in1_offset = 0
        self._in2_offset = 0 
        self._in3_offset = 0
        self._out_offset = 0


    def fill_attributes(self, onnx_node):
        for attr in onnx_node.attribute:
            if attr.name == "auto_pad":
                self._autopad = attr.s
            if attr.name == "dilations":
                self._dilations = attr.ints
            if attr.name == "group":
                self._group = int(attr.i)
            if attr.name == "kernel_shape":
                self._kernel_shape = attr.ints
            if attr.name == "pads":
                self._pads = attr.ints
            if attr.name == "strides":
                self._strides = attr.ints



    def map(self, memory_mapper):
        self._in1_offset = memory_mapper.map(self._in1_flat)
        self._in2_offset = memory_mapper.map(self._in2_flat)
        self._out_offset = memory_mapper.map(self._out_flat)
        if self._in3_flat is not None:
            self._in3_offset = memory_mapper.map(self._in3_flat)
        self._inputs2mem(memory_mapper)

    def unmap(self, memory_mapper):
        self._mem2output(memory_mapper)
        memory_mapper.unmap(self._in1_flat)
        memory_mapper.unmap(self._in2_flat)
        memory_mapper.unmap(self._out_flat)
        if self._in3_flat is not None:
            memory_mapper.unmap(self._in3_flat)

    def _inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._in1_flat, self._in1_offset)
        memory_xfer_engine.sys2mem(self._in2_flat, self._in2_offset)
        if self._in3_flat is not None:
            memory_xfer_engine.sys2mem(self._in3_flat, self._in3_offset)

    def _mem2output(self, memory_xfer_engine):
        memory_xfer_engine.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._out_shape)
            self._outputs[0][multi_index] = self._out_flat[i]


    def compile(self, source, destinations):

        tile_commands = list()

        batch_size = self._in1_shape[0]
        num_channels = self._in1_shape[1]
        num_feature_maps = self._in2_shape[0]
        out_shape = self._out_shape

        num_destinations = len(destinations)
        which_dest = 0

        for b in range(batch_size):
            for m in range(num_feature_maps):
                o0 = 0
                i0 = 0
                while o0 < self._out_shape[2]:

                    o1 = 0
                    i1 = 0 
                    while o1 < self._out_shape[3]:
                        in_addrs = list()
                        wt_addrs = list()
                        destination = destinations[which_dest]

                        out_idx = self.ravel_multi_index([b, m, o0, o1], out_shape) + self._out_offset
                        attributes = {
                            "res_addr" : out_idx,
                            "operation" : Operator.ADD,
                            "dtype" : self._out_flat.dtype,
                            "op1" : 0,
                            "op2" : 0
                        }                        
                        message_stamp = uuid.uuid4()
                        tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                        tile_commands.append(tile_command)

                        for c in range(num_channels):
                            for kern0 in range(self._kernel_shape[0]):
                                for kern1 in range(self._kernel_shape[1]):

                                    ii0 = i0 + kern0 + self._dilations[0] -1 
                                    if ii0 < 0 or ii0 >= self._in1_shape[2]:
                                        continue
                                    ii1 = i1 + kern1 + self._dilations[1] -1 
                                    if ii0 < 0 or ii0 >= self._in1_shape[3]:
                                        continue

                                    in_addrs.append(self.ravel_multi_index([b, c, i0+kern0, i1+kern1], self._in1_shape) + self._in1_offset)
                                    wt_addrs.append(self.ravel_multi_index([m, c, kern0, kern1], self._in2_shape) + self._in2_offset)

                        attributes = {
                            "res_addr" : out_idx,
                            "operation" : Operator.DOT,
                            "dtype" : self._out_flat.dtype,
                            "col_addrs" : in_addrs,
                            "row_addrs" : wt_addrs,
                        }

                        if self._in3_flat is not None:
                            attributes["bias"] = self.ravel_multi_index([i,j], out_shape) + self._in3_offset
                        message_stamp = uuid.uuid4()
                        tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                        tile_commands.append(tile_command)

                        which_dest += 1
                        which_dest = which_dest % num_destinations

                        i1 += self._strides[1]
                        o1 += 1

                    i0 += self._strides[0]
                    o0 += 1

        return tile_commands
