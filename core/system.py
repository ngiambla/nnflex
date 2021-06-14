from core.clock import Clock


class System:
	'''

	'''
	def __init__(self):
		self._system_clock_ref = Clock(self)


	def xfer_from_host(self):
		'''
		'''
		raise NotImplementedError("Please specialize according to the Accelerator Specification")



	def xfer_to_host(self):
		'''
		'''
		raise NotImplementedError("Please specialize according to the Accelerator Specification")
		


	def process(self, operation, dataflow):
		'''
		'''
		raise NotImplementedError("Please specialize according to the Accelerator Specification")