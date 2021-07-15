'''clock.py

Modules which either implements or holds reference to the clock-cycle count

Author: Nicholas V. Giamblanco
Date: June 16, 2021

'''

class Clock:
	''' Clock:
		An object which represents the clock of a hardware system.

		Technically, a system could have more than one clock... but you'd likely need 
		a mechanism to deal with cross domain crossing.
	'''
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
		''' Returns the current clock count.
		'''
		return self._clock


class ClockReference:
	''' ClockReference:

	Holds reference to the Clock object.
	'''
	def __init__(self, clock):
		if not isinstance(clock, Clock):
			raise ValueError("ClockReference can only reference a Clock object.")
		self._clock_ref = clock


	def current_clock(self):
		return self._clock_ref.current_clock()
