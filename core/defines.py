''' defines.py
'''
from enum import Enum

class DType(Enum):
    FP16 = 16
    FP32 = 32
    FP64 = 64
    I8 = 8
    I16 = 16
    I32 = 32
    I64 = 64

class Operator(Enum):
    ADD = 1
    SUB = 2
    MUL = 3
    DIV = 4
    MAC = 5
    CLEAR = 6
    MAX = 7
    MIN = 8
    DOT = 9




def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])