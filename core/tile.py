

class Tile:
	'''
	
	'''
    def __init__(self, system_clock_ref, interconnect):
    	self._system_clock_ref = system_clock_ref
    	self._interconnect = interconnect

		
	def process(self):
		'''
		'''
		raise NotImplementedError("Please specialize according to the Accelerator Specification")
