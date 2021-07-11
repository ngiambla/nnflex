''' utils.py
'''
import struct

def float_to_int_repr_of_float(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]


def int_repr_of_float_to_float(i):
    return struct.unpack('<f', struct.pack('<I', i))[0]


def flatten(t):
    return [item for sublist in t for item in sublist]