'''
'''
from operators.flexnode import FlexNode

class SpatialFilter(FlexNode):

	def __init__(self, onnx_node, onnx_name, op_name):
		FlexNode.__init__(self, onnx_node, onnx_name, op_name)

		# References to Input Tensors
		self._input = None
		self._weight = None 

		# References to Output Tensors
		self._output = None

		self._group = None 
		self._kernel_shape = list()
		self._dilations = list()
		self._pads = list()
		self._strides = list()
		self._auto_pad = "NOTSET"


	def fill_attributes(onnx_node):
		pass

