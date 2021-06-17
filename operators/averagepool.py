'''
'''
from operators.flexnode import FlexNode
from core.defines import Operator

class AveragePool(FlexNode):

	def __init__(self, onnx_node, onnx_name):
		FlexNode.__init__(self, onnx_node, onnx_name, "AveragePool")

