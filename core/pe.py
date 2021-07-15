''' pe.py
'''

from transitions import Machine, State

from core.device import Device

class PE(Device):
    '''PE: An abstraction on a Processing Element

    Note:
        Since this is an abstract class, the `process` method is not integrated.

    Args:
        message_router: A MessageRouter object, which handles communication between the PE and other sys. components
        message_queue_size: If desired, the MessageRouter can hold message for the PE.

    '''
    def __init__(self, system_clock_ref, message_router, message_queue_size = 1):
        Device.__init__(self, system_clock_ref, message_router, message_queue_size)


    def process(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator-PE-Specification")




