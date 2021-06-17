'''
'''
from operators.flexnode import FlexNode
from core.defines import Operator

class Arithmetic(FlexNode):

	def __init__(self, onnx_node, inputs):
		FlexNode.__init__(self, onnx_node, )

		if operation == "Div":
			self._operation = Operator.DIV
		elif operation == "Add":
			self._operation = Operator.ADD
		elif operation == "Mul":
			self._operation = Operator.MUL
		else:
			raise NotImplementedError("Operator: "+str(operation)+" is not implememted.")


	def compile()