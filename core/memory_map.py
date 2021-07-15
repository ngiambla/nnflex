''' memory_map.py: 

Classes which map a Numpy array to nnflex's Memory class (and specializations)

Author: Nicholas V. Giamblanco
Date: June 16, 2021

'''
import numpy
import struct
from core.allocator import BitAlloc
from core.utils import *


class MemoryMapper:
    ''' MemoryMapper: a class which can map a numpy array into a memory-device.
    Using BitAlloc from core.allocator (any allocator would suffice),
    We map a numpy array to memory via .nditer
    '''
    def __init__(self, memory_system, memory_size, word_size):
        self._memory_system = memory_system
        self._memory_map = dict()
        self._allocator = BitAlloc(memory_size, word_size)

    def map(self, array):
        ''' map:

        Given a numpy array, maps this into valid memory-locations

        Notes:
            self._allocator.alloc(nbytes) can return None,
            indicating that the memory does not have enough memory
            to service the allocation. We raise a runtime error if that's the case.

        Args:
            array: A numpy array

        Returns:
            an integer representing the beginning of the offset of the array location
            in memory.

        '''
        array_id = id(array)
        self._memory_map[array_id] = self._allocator.alloc(array.nbytes)
        if self._memory_map[array_id] is None:
            raise RuntimeError("Memory Device: Out of memory")
        return self._memory_map[array_id]


    def is_mapped(self, array):
        ''' is_mapped:

        Will check if the array has been mapped into memory already.

        Args:
            array: A numpy array

        Returns:
            A boolean response indicating if the array is mapped into memory.
        '''
        return id(array) in self._memory_map

    def lookup(self, array):
        ''' lookup:

        Fetches the offset in memory for the requested array.

        Notes:
            If the array was never mapped, a ValueError is raised.

        Args:
            array: A numpy array

        Returns:
            An integer representing the array's offset into memory.
        '''
        array_id = id(array)
        if array_id not in self._memory_map:
            raise ValueError("Array was not mapped into memory.")
        return self._memory_map[array_id]


    def unmap(self, array):
        '''
        '''
        array_id = id(array)
        if array_id not in self._memory_map:
            raise ValueError("Array was not mapped into memory.")

        addr = self._memory_map[array_id]
        self._allocator.free(addr)
        del self._memory_map[array_id]


    def sys2mem(self, arr, offset):
        '''
        '''
        for i in range(len(arr)):
            data = float_to_int_repr_of_float(arr[i])
            self._memory_system._poke(i+offset, data)

    def mem2sys(self, arr, offset):
        for i in range(len(arr)):
            arr[i] = int_repr_of_float_to_float(self._memory_system._peek(i+offset))


