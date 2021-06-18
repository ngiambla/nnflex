'''

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
        raise NotImplementedError("Specializations must specify this.")


    def unmap(self, memory_mapper):
        raise NotImplementedError("Specializations must specify this.")


    def inputs2mem(self, memory_xfer_engine):
        raise NotImplementedError("Specializations must specify this.")


    def mem2output(self, memory_xfer_engine):
        raise NotImplementedError("Specializations must specify this.")


    def compile(self, source, destination):
        raise NotImplementedError("Specializations must specify this.")


    def fill_attributes(self):
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