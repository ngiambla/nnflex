'''system.py

'''

# Python Imports
from time import perf_counter

# nnflex Imports.
from core.clock import Clock, ClockReference


class System:
    ''' An abstract class that represents an accelerator system.

    Notes:
        The System defines an internal clock, which is propagated through-out 
        the entire network.

    Returns:
        A "Memory" object.

    '''
    def __init__(self):
        self._system_clock = Clock()
        self._system_clock_ref = ClockReference(self._system_clock)


    def process(self):
        ''' Processes the system state for 1 clock cycle (i.e., 1 tick)
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def forward(self):
        ''' Executes the forward pass of a neural network layer on the accelerator.
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")  

    def backward(self):
        ''' Executes the backward pass of a neural network layer on the accelerator.
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def collect_statistics(self):
        ''' 
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")


    def tick(self):
        ''' Moves the system clock count forward 1 tick.
        '''
        self._system_clock.clock()


