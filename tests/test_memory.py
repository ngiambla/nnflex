'''test_memory.py:

Tests the memory object behaves as expected.
'''

import pytest


from core.memory import Memory

from core.clock import Clock, ClockReference
from core.message_router import MessageRouter



@pytest.mark.parametrize("system_clock_ref", [None, -1.0, -1])
@pytest.mark.parametrize("message_router", [None, -1.0, -1])
@pytest.mark.parametrize("message_queue_size", [None, -1.0, -1])
@pytest.mark.parametrize("log_transactions", [None, -1.0, -1])
@pytest.mark.parametrize("word_byte_size", [None, -1.0, -1])
@pytest.mark.parametrize("width", [None, -1.0, -1])
def test_memory_instantiation_invalid(system_clock_ref, message_router, message_queue_size, log_transactions, word_byte_size, width):
	result = False
	try:
		Memory(system_clock_ref, message_router, message_queue_size, log_transactions, word_byte_size, width)
	except ValueError as VE:
		result = True

	assert result


@pytest.mark.parametrize("addr", [-1, 0, 4, 3.0])
def test_memory_peek_invalid(addr):
	clock = Clock()
	clock_ref = ClockReference(clock)
	router = MessageRouter(clock_ref)

	memory = Memory(clock_ref, router, 1, False, 4, 4)
	result = False
	try:
		memory._peek(addr)
	except ValueError as VE:
		result = True

	assert result

@pytest.mark.parametrize("addr", [-1, 4, 3.0])
def test_memory_poke_invalid(addr):
	clock = Clock()
	clock_ref = ClockReference(clock)
	router = MessageRouter(clock_ref)
	memory = Memory(clock_ref, router, 1, False, 4, 4)

	result = False
	try:
		memory._poke(addr, 0xDEADBEAF)
	except ValueError as VE:
		result = True

	assert result


@pytest.mark.parametrize("addrs", [[1,2,3,4], [3,1,2,5]])
def test_memory_poke_peek(addrs):
	clock = Clock()
	clock_ref = ClockReference(clock)
	router = MessageRouter(clock_ref)
	memory = Memory(clock_ref, router, 1, False, 4, 400)

	for addr in addrs:
		result = True
		try:
			memory._poke(addr, 0xDEADBEAF)
			assert memory._peek(addr) == 0xDEADBEAF
		except ValueError as VE:
			result = False

		assert result


@pytest.mark.parametrize("addrs", [[1,2,3,4], [3,1,2,5]])
def test_memory_poke_peek_log(addrs):
	clock = Clock()
	clock_ref = ClockReference(clock)
	router = MessageRouter(clock_ref)
	memory = Memory(clock_ref, router, 1, True, 4, 400)

	log_string = ""
	for addr in addrs:
		result = True
		try:
			log_string += ('0x%08x' % addr) + " write 0\n"
			memory._poke(addr, 0xDEADBEAF)
			log_string += ('0x%08x' % addr) + " read 0\n"

			assert memory._peek(addr) == 0xDEADBEAF
		except ValueError as VE:
			result = False

		assert result
	true_log = ""
	for transaction in memory._transaction_log:
		true_log += transaction + "\n"
	assert true_log == log_string