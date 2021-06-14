'''clock.py
'''

class Clock:
	def __init__(self, top_level_device):
		self._top_level_device = top_level_device
		self._clock = 0

	def clock(self, top_level_device):
		''' clock will increment the clock count

		Note: 
			The clock count will only be incremented if and only if the
			top-level devices issues the request.
		'''
		if top_level_device == self._top_level_device:
			self._clock += 1

	def current_clock(self):
		return self._clock