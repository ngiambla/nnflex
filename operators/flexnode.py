''' flexnode.py

Implements the data-structure which will encompass and inflate an ONNX node for use with NNFlex's messaging system.
'''
import numpy as np

class FlexNode:

    def __init__(self, onnx_node, inputs, outputs):
        self._onnx_node = onnx_node
        self._inputs = inputs
        self._outputs = outputs

    def get_op_name(self):
        return self._onnx_node.name

    def get_op_type(self):
        return self._onnx_node.op_type

    def map(self, memory_mapper):
        ''' map: Maps all numpy arrays into the memory-system referenced by memory_mapper via
                NNFlex's memory-allocator.
        Args:
            memory_mapper: MemoryMapper object configured with an accelerator's memory system and allocator.
        '''
        raise NotImplementedError("Specializations must specify this.")


    def unmap(self, memory_mapper):
        ''' unmap: Unmaps all numpy arrays from the memory-system referenced by memory_mapper via
                NNFlex's memory-allocator.
        Args:
            memory_mapper: MemoryMapper object configured with an accelerator's memory system and allocator.
        '''
        raise NotImplementedError("Specializations must specify this.")


    def _inputs2mem(self, memory_xfer_engine):
        ''' This internal functions conducts the actual data transfer from numpy-array
        to memory-system.
        Args:
            memory_xfer_engine: MemoryMapper object configured with an accelerator's memory system and allocator.        
        '''        
        raise NotImplementedError("Specializations must specify this.")


    def _mem2output(self, memory_xfer_engine):
        ''' This internal functions conducts the actual data transfer from the memory-system to 
        the corresponding numpy arrays.
        Args:
            memory_xfer_engine: MemoryMapper object configured with an accelerator's memory system and allocator.                 
        '''        
        raise NotImplementedError("Specializations must specify this.")


    def compile(self, source, destinations):
        ''' Compiles the computations for the FlexNode as Tile Messages.

        Args:
            source: the Device which is sending the messages.
            destinations: a list of all possible destination devices which can compute this.
        '''
        raise NotImplementedError("Specializations must specify this.")


    def fill_attributes(self):
        ''' When translating the ONNX node to a FlexNode, we MUST interpret any of it's attributes
        as it will impact how the computation operates.
        '''
        raise NotImplementedError("Specializations must specify this if required.")


    def ravel_multi_index(self, indexes, dims):
        ''' ravel_multi_index:

        Converts a tuple of indices used to index into a multi-dim array
        into a flatten-array index equivalent: 
        >>> arr = np.arange(1, 10).reshape(3, 3)
        >>> arr
        array([[ 1,  2,  3],
               [ 4,  5,  6],
               [ 7,  8,  9]])

        >>> arr[1, 2]
        6

        >>> arr_flat = arr.flatten()
        array([1, 2, 3, 4, 5, 6, 7, 8, 9])

        >>> arr_flat[5]
        6

        >>> np.ravel_multi_index((1,2), (3,3)
        5

        Ref:
            https://numpy.org/doc/stable/reference/generated/numpy.ravel_multi_index.html#numpy.ravel_multi_index

        '''
        return np.ravel_multi_index(tuple(indexes), tuple(dims))

    def unravel_index(self, index, dims):
        ''' unravel_index:

        Maps an index intended for flatten variant of an array into the row/col index format
        for the specified dims.
        
        Ref: 
            https://numpy.org/doc/stable/reference/generated/numpy.unravel_index.html#numpy.unravel_index
        '''
        return np.unravel_index(index, tuple(dims))