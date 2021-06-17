'''clock.py

Modules which either implements or holds reference to the clock-cycle count

Author: Nicholas V. Giamblanco
Date: June 16, 2021

'''

class Clock:
	def __init__(self):
		self._clock = 0

	def clock(self):
		''' clock will increment the clock count

		Note: 
			The clock count will only be incremented if and only if the
			top-level devices issues the request.
		'''
		self._clock += 1

	def current_clock(self):
		return self._clock


class ClockReference:
	def __init__(self, clock_ref):
		self._clock_ref = clock_ref

	def current_clock(self):
		return self._clock_ref.current_clock()
