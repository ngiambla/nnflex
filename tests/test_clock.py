from core.clock import Clock, ClockReference


def test_clock_instantiation():
	# flag to assert
	result = False

	# Clock object instantiation
	clock = Clock()

	# Test the object is not None.
	if clock is not None and clock.current_clock() == 0:
		result = True

	assert result


def test_clock_clock():
	# flag to assert
	result = False

	# Clock object instantiation
	clock = Clock()

	clock.clock()

	if clock.current_clock() == 1:
		result = True

	assert result


def test_clock_reference_no_clock():
	result = False

	try:
		clock_ref = ClockReference(None)
	except ValueError as VE:
		result = True

	assert result

def test_clock_reference_cannot_clock():
	result = False

	# Clock object instantiation
	clock = Clock()

	clock_ref = ClockReference(clock)
	try:
		clock_ref.clock()
	except AttributeError as AE:
		result = True

	assert result


def test_clock_reference_tracks_clock():
	result = False

	# Clock object instantiation
	clock = Clock()

	clock_ref = ClockReference(clock)

	clock.clock()

	if clock_ref.current_clock() == 1:
		result = True

	assert result	
