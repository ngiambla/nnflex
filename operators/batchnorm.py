''' batchnorm.py:

Implement's the BatchNormalization ONNX node as a flexnode (for use with any accelerator)

From the ONNX Operator guide: Y = (X - input_mean) / sqrt(input_var + epsilon) * scale + B


'''
import uuid

import numpy as np

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class BatchNorm(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)
        # Attributes
        self._epsilon = 1e-5
        self._momentum = 0.9
        self._training_mode = 0

        # Inputs
        self._scale = self._inputs[1]

        self._bias = self._inputs[2]
        self._bias_offset = 0
        
        self._mean = self._inputs[3]
        self._variance = self._inputs[4]

        # Outputs
        self._out_shape = None
        self._out_flat =  None
        self._out_offset = 0

        self.fill_attributes(onnx_node)


    def fill_attributes(self, onnx_node):
        for attr in onnx_node.attribute:
            if attr.name == "epsilon":
                self._epsilon = attr.f
            if attr.name == "momentum":
                self._momentum = attr.f
            if attr.name == "training_mode":
                self._training_mode = int(attr.i)
                if self._training_mode == 1:
                    raise NotImplementedError("We currently do not support training.")
    

    def map(self, memory_mapper):

        out = self._outputs[0]
        self._out_shape = out.shape
        self._out_flat = out.flatten()        

        self._bias_offset  = memory_mapper.map(self._bias)
        self._out_offset = memory_mapper.map(self._out_flat)
        self._inputs2mem(memory_mapper)


    def unmap(self, memory_mapper):
        self._mem2output(memory_mapper)

        memory_mapper.unmap(self._bias)
        memory_mapper.unmap(self._out_flat)

    def _inputs2mem(self, memory_xfer_engine):
        memory_xfer_engine.sys2mem(self._bias, self._bias_offset)
        memory_xfer_engine.sys2mem(self._out_flat, self._out_offset)


    def _mem2output(self, memory_xfer_engine):
        memory_xfer_engine.mem2sys(self._out_flat, self._out_offset)
        for i in range(len(self._out_flat)):
            multi_index = self.unravel_index(i, self._out_shape)
            self._outputs[0][multi_index] = self._out_flat[i]


    def compile(self, source, destinations):

        tile_commands = list()

        batch_size = self._in1_shape[0]
        num_channels = self._in1_shape[1]
        height = self._in1_shape[2]
        width = self._in1_shape[3]

        out_shape = self._out_shape

        num_destinations = len(destinations)
        which_dest = 0

        seen_output = set()

        for b in range(batch_size):
            for c in range(num_channels):
                for h in range(height):
                    for w in range(width):
                        #From the ONNX Operator guide: Y = (X - input_mean) / sqrt(input_var + epsilon) * scale + B

                        destination = destinations[which_dest]

                        out_idx = self.ravel_multi_index([b, c, h, w], out_shape) + self._out_offset
                        if out_idx not in seen_output:
                            seen_output.add(out_idx)
                        else:
                            raise ValueError("Seen this output before: "+str(seen_output))

                        op1 = (self._input[b][c][h][w]-self._mean[c])/np.sqrt(self._variance[c] + self._epsilon[c]) *self._scale[c]
                        attributes = {
                            "res_addr" : out_idx,
                            "operation" : Operator.ADD,
                            "dtype" : self._out_flat.dtype,
                            "op1" : op1,
                            "op2_addr" : self._bias_offset + c,
                        }

                        message_stamp = uuid.uuid4()
                        tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
                        tile_commands.append(tile_command)
                        which_dest += 1
                        which_dest = which_dest % num_destinations                        

        return tile_commands
