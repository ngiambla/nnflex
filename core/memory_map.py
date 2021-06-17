''' memory_map.py: 

Classes which map a Numpy array to nnflex's Memory class (and specializations)

Author: Nicholas V. Giamblanco
Date: June 16, 2021

'''
import numpy
from core.allocator import BitAlloc


class MemoryMapper:
    ''' MemoryMapper: a class which can map a numpy array into a memory-device.
    Using BitAlloc from core.allocator (any allocator would suffice),
    We map a numpy array to memory via .nditer
    '''
    def __init__(self, memory_size, word_size):
        self._memory_map = dict()
        self._allocator = BitAlloc(memory_size, word_size)

    def map(self, array):
        array_id = id(array)
        self._memory_map[array_id] = self._allocator.alloc(array.nbytes)


    def lookup(self, array):
        array_id = id(array)
        if array_id not in self._memory_map:
            raise ValueError("Array was not mapped into memory.")
    	return self._memory_map[array_id]


    def unmap(self, array):
        array_id = id(array)
        if array_id not in self._memory_map:
            raise ValueError("Array was not mapped into memory.")

        addr = self._memory_map[array_id]
        self._allocator.free(addr)
        del self._memory_map[array_id]

    	
