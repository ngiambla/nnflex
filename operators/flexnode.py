'''

'''
class FlexNode:

	def __init__(self, onnx_node):
		self._onnx_node = onnx_node
		self._op_name = op_name

	def get_op_name(self):
		return self._onnx_node.name


	def compile(self):
		raise NotImplementedError("")
