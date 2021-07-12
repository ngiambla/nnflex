''' pooling.py:

Implement's {Max, Average}Pool ONNX node as a flexnode (for use with any accelerator)

'''
import itertools
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Pooling(FlexNode):

    def __init__(self, onnx_node, inputs, outputs, specialization):
        FlexNode.__init__(self, onnx_node, inputs, outputs)


        self._specialization = "Avg"
        self._operation = Operator.ADD

        if specialization == "Max":
            self._specialization = specialization
            self._operation = Operator.MAX

        self._autopad = "NOTSET"
        self._dilations = None
        self._group = 1
        self._kernel_shape = None
        self._pads = None
        self._strides = None

        self.fill_attributes(onnx_node)

        self._in1_shape = None
        self._in1_flat = None
        
        self._out_shape = None
        self._out_flat =  None

        self._in3_shape = None
        self._in3_flat = None

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

        in1 = self._inputs[0]
        self._in1_shape = in1.shape
        self._in1_flat = in1.flatten()

        out = self._outputs[0]
        self._out_shape = out.shape
        self._out_flat = out.flatten()


        self._in1_offset = memory_mapper.map(self._in1_flat)
        self._out_offset = memory_mapper.map(self._out_flat)

        self._inputs2mem(memory_mapper)

    def unmap(self, memory_mapper):
        self._mem2output(memory_mapper)

        memory_mapper.unmap(self._in1_flat)
        memory_mapper.unmap(self._out_flat)

    def _inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._in1_flat, self._in1_offset)

    def _mem2output(self, memory_xfer_engine):
        memory_xfer_engine.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._out_shape)
            self._outputs[0][multi_index] = self._out_flat[i]

    def compile(self, source, destinations):

        tile_commands = list()

        batch_size = self._in1_shape[0]
        num_channels = self._in1_shape[1]
        out_shape = self._out_shape

        num_destinations = len(destinations)
        which_dest = 0

        seen_output = set()

        for b in range(batch_size):
            for m in range(num_channels):
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
                        if out_idx not in seen_output:
                            seen_output.add(out_idx)
                        else:
                            raise ValueError("Seen this output before: "+str(seen_output))

                        for kern0 in range(self._kernel_shape[0]):
                            for kern1 in range(self._kernel_shape[1]):

                                ii0 = i0 + kern0 + self._dilations[0] -1 
                                if ii0 < 0 or ii0 >= self._in1_shape[2]:
                                    continue
                                ii1 = i1 + kern1 + self._dilations[1] -1 
                                if ii0 < 0 or ii0 >= self._in1_shape[3]:
                                    continue

                                in1 = self.ravel_multi_index([b, c, i0+kern0, i1+kern1], self._in1_shape) + self._in1_offset

                                attributes = {
                                    "res_addr" : out_idx,
                                    "operation" : self._operation,
                                    "dtype" : self._out_flat.dtype,
                                    "in1_addr" : out_idx,
                                    "in2_addr" : in1,
                                }

                                message_stamp = uuid.uuid4()
                                tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                                tile_commands.append(tile_command)

                        if self._specialization == "AVG":
                            # This implies tha
                            attributes = {
                                "res_addr" : out_idx,
                                "operation" : Operator.DIV,
                                "dtype" : self._out_flat.dtype,
                                "in1_addr" : out_idx,
                                "in2" : self._kernel_shape[0]*self._kernel_shape[1],
                            }

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
