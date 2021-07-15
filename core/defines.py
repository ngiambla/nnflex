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
    CMAC = 6
    CLEAR = 7
    MAX = 8
    MIN = 9
    DOT = 10
    POW = 11
