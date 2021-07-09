''' arithemtic.py:

Implement's the arithmetic ONNX node as a flexnode (for use with any accelerator)

'''
import uuid


from operators.flexnode import FlexNode
from core.defines import Operator
from core.messaging import Message
  
class Arithmetic(FlexNode):

	def __init__(self, onnx_node, inputs, outputs):
		FlexNode.__init__(self, onnx_node, inputs, outputs)

		in1 = self._inputs[0]
		in2 = self._inputs[1]
		out = self._outputs[0]

		self._in1_flat = in1.flatten()
		self._in2_flat = in2.flatten()
		self._out_flat = out.flatten()

		self._length = len(self._in1_flat)

		self._in1_offset = 0
		self._in2_offset = 0 
		self._out_offset = 0

		if operation == "Div":
			self._operation = Operator.DIV
		elif operation == "Add":
			self._operation = Operator.ADD
		elif operation == "Mul":
			self._operation = Operator.MUL
		else:
			raise NotImplementedError("Operator: "+str(operation)+" is not implememted.")


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
		memory_xfer_engine.mem2sys(self._out_flat, self._out_offset)
		for i in range(len(self._out_flat)):
			multi_index = self.unravel_index(i, self._outputs[0].shape)
			self._outputs[0][multi_index] = self._out_flat[i]

	def compile(self, source, destinations):
		'''
		'''

		tile_commands = list()
        num_destinations = len(destinations)
        which_dest = 0
        
		for i in range(len(self._length)):
            op1_addr = self._in1_offset+i
            op2_addr = self._in2_offset+i
            res_addr = self._out_offset+i
            attributes = {
                "op1_addr" : op1_addr,
                "op2_addr" : op2_addr,
                "res_addr" : res_addr,
                "operation" : self._operation,
                "dtype" : self._out_flat.dtype
            }
            destination = destinations[which_dest]
            message_stamp = uuid.uuid4()
            tile_command = Message(source, destination, Message.TileCmd, message_stamp, attributes=attributes)
            tile_commands.append(tile_command)
            which_dest += 1
            which_dest = which_dest % num_destinations

        return tile_commands
