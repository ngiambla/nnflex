''' utils.py
'''
import struct

def float_to_int_repr_of_float(f):
    ''' Given a 32-bit floating-point number,
    convert the value into it's IEEE Binary representation.
    Args:
        f: 32-bit floating-point number
    '''
    return struct.unpack('<I', struct.pack('<f', f))[0]


def int_repr_of_float_to_float(i):
    ''' Given an integer, treat the integer as a IEEE Binary representation
    and convert the representation into a 32-bit floating point number.
    Args:
        i: 32-bit integer.
    '''
    return struct.unpack('<f', struct.pack('<I', i))[0]


def flatten(t):
    ''' provided with a two dimensional list, flatten the list into a 1-d list.
    '''
    return [item for sublist in t for item in sublist]