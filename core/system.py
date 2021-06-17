'''system.py

'''

# Python Imports
from time import perf_counter

# nnflex Imports.
from core.clock import Clock, ClockReference


class System:
    '''

    '''
    def __init__(self):
        self._system_clock = Clock()
        self._system_clock_ref = ClockReference(self._system_clock)


    def xfer_from_host(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def xfer_to_host(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")
        

    def process(self, operation, dataflow):
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


    def collect_statistics(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def tick(self):
        self._system_clock.clock()


