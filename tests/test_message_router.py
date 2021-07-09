'''test_message_router.py:

Tests for the MessageRouter object
'''

import pytest

from core.device import Device
from core.messaging import Message
from core.message_router import MessageRouter
from core.clock import Clock, ClockReference

def test_message_router_instantiation_valid():
	clock = Clock()
	clock_ref = ClockReference(clock)
	msg_router = MessageRouter(clock_ref)
	assert True


def test_message_router_instantiation_invalid():
	result = False
	try:
		msg_router = MessageRouter(None)
		print(msg_router)
	except ValueError as VE:
		result = True

	assert result


@pytest.mark.parametrize("queue_size", [1, 2, 3, 4])
def test_message_router_send(queue_size):
	clock = Clock()
	clock_ref = ClockReference(clock)
	msg_router = MessageRouter(clock_ref)

	sender = Device(clock_ref, msg_router)
	receiver = Device(clock_ref, msg_router, queue_size)
	
	msg = Message(sender, receiver, Message.Ping)
	for i in range(0, queue_size):
		assert msg_router.send(msg)
	assert not msg_router.send(msg)


@pytest.mark.parametrize("queue_size", [1, 2, 3, 4])
def test_message_router_send_and_fetch(queue_size):
	clock = Clock()
	clock_ref = ClockReference(clock)
	msg_router = MessageRouter(clock_ref)

	sender = Device(clock_ref, msg_router)
	receiver = Device(clock_ref, msg_router, queue_size)
	
	msg = Message(sender, receiver,  Message.Ping)
	for i in range(0, queue_size):
		assert msg_router.send(msg)
	assert not msg_router.send(msg)

	for i in range(0, queue_size):
		assert msg_router.fetch(receiver) is not None
	assert msg_router.fetch(receiver) is None

