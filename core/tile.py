''' tile.py
'''

class Tile:
    '''
    
    '''
    def __init__(self, system_clock_ref, interconnect, data_queue_size = 2):
        self._system_clock_ref = system_clock_ref
        self._interconnect = interconnect
        self._interconnect.add_connection(self, data_queue_size)
        

        
    def process(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")

    def forward(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")  

    def backward(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")        
