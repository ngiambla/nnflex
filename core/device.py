''' device.py
'''

from transitions import Machine
from core.clock import ClockReference
from core.message_router import MessageRouter

class Device:
    ''' Device:

    A base class that all accelerator components inherit from.
    A device requires a clock-reference and a message-router (to communicate)

    Args:
        system_clock_ref: a ClockReference object, should be from the System.
        message_router: a MessageRouter object; this Router should have connections to 
                        other Devices with which THIS device needs to communicate with.
        message_queue_size: Implements a FIFO on the MessageRouter port for this device to 
                            save messages (if the device is busy and cannot accept a message)
    '''
    def __init__(self, system_clock_ref, message_router, message_queue_size = 1):

        if not isinstance(system_clock_ref, ClockReference):
            raise ValueError("A ClockReference must be supplied, not: "+str(system_clock_ref))

        self._system_clock_ref = system_clock_ref

        if not isinstance(message_router, MessageRouter):
            raise ValueError("A MessageRouter must be supplied, not: "+str(message_router))

        self._message_router = message_router
        self._message_router.add_connection(self, message_queue_size)

        self._num_stalls = 0

    def number_of_stalled_cycles(self):
        '''
        '''
        return self._num_stalls