''' device.py
'''

from transitions import Machine
from core.clock import ClockReference
from core.message_router import MessageRouter

class Device:
    '''

    '''
    def __init__(self, system_clock_ref, message_router, message_queue_size = 1):

        if not isinstance(system_clock_ref, ClockReference):
            raise ValueError("A ClockReference must be supplied, not: "+str(system_clock_ref))

        self._system_clock_ref = system_clock_ref

        if not isinstance(message_router, MessageRouter):
            raise ValueError("A MessageRouter must be supplied, not: "+str(message_router))

        self._message_router = message_router
        self._message_router.add_connection(self, message_queue_size)
