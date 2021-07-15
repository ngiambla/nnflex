''' softmax.py


Softmax(input, axis) = Exp(input) / ReduceSum(Exp(input), axis=axis, keepdims=1)

'''

import uuid
import itertools

from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Softmax(FlexNode):

    def __init__(self, onnx_node, inputs, outputs):
        FlexNode.__init__(self, onnx_node, inputs, outputs)

        # Attributes.
        self._axis = None

        # Inputs
        self._in1_shape = None
        self._in1_flat = None
        self._in1_offset = 0

        # Outputs
        self._out_shape = None
        self._out_flat = None        
        self._out_offset = 0

        self.fill_attributes(onnx_node)


    def fill_attributes(self, onnx_node):
        for attr in onnx_node.attribute:
            if attr.name == "axis":
                self._axis = attr.i


    def map(self, memory_mapper):
        in1 = self._inputs[0]
        out = self._outputs[0]

        self._in1_shape = in1.shape
        self._in1_flat = in1.flatten()

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
            multi_index = self.unravel_index(i, self._outputs[0].shape)
            self._outputs[0][multi_index] = self._out_flat[i]

    def compile(self, source, destinations):
        '''
        '''

        tile_commands = list()
        
        dims = len(self._in1_shape)

        num_destinations = len(destinations)
        which_dest = 0

        for i in range(len(self._in1_flat)):
            op1_addr = self._in1_offset+i
            res_addr = self._out_offset+i
            attributes = {
                "op1" : 2.71828,
                "op2_addr" : op1_addr,
                "res_addr" : res_addr,
                "operation" : Operator.POW,
                "dtype" : self._out_flat.dtype
            }
            destination = destinations[which_dest]
            message_stamp = uuid.uuid4()
            tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
            tile_commands.append(tile_command)
            which_dest += 1
            which_dest = which_dest % num_destinations

        softmax_denom = np.sum(np.exp(self._inputs[0]), axis=self._axis, keepdims=1).flatten()

        for i in range(len(softmax_denom)):
            res_addr = self._out_offset+i
            attributes = {
                "op1_addr" : res_addr,
                "op2" : softmax_denom[i],
                "res_addr" : res_addr,
                "operation" : Operator.POW,
                "dtype" : self._out_flat.dtype
            }
            destination = destinations[which_dest]
            message_stamp = uuid.uuid4()
            tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
            tile_commands.append(tile_command)
            which_dest += 1
            which_dest = which_dest % num_destinations

        return tile_commands
