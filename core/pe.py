from defines import DType, Operator

class PE:
    '''PE: An abstraction on a Processing Element

    Note:
        Since this is an abstract class, the `process` method is not
        integrated.

    Args:
        interconnect: An interconnect object, which determins what the PE can communicate with

    '''
    def __init__(self, system_clock_ref, interconnect, queue_size = 1):
        self._system_clock_ref = system_clock_ref
        self._interconnect = interconnect
        self._interconnect.add_connection(self, queue_size)


    def process(self):
        raise NotImplementedError("Please specialize according to the Accelerator-PE-Specification")
