''' tile.py
'''

from core.device import Device

class Tile(Device):
    ''' Tile:

    Notes:
        Since this is a base class, 

    Args:


    Returns:
        A Tile object.
    
    '''
    def __init__(self, system_clock_ref, message_router, message_queue_size = 2):
        self._system_clock_ref = system_clock_ref
        self._message_router = message_router
        self._message_router.add_connection(self, message_queue_size)
        

        
    def process(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def collect_statistics(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")