''' compackets.py: Packets to be sent between compute elements

There are three specializations, specifically:
(1) MemWritePacket: A packet representing a request to write to memory
(2) MemReadPacket: A packet representing a request to read to memory.
(3) DataPacket: A packet representing a data xfer

'''


class ComPacket:
    '''ComPacket: The Base Class that all packets should inherit from

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.

    Returns:
        a ComPacket object

    '''
    def __init__(self, source, destination):
        self._source = source
        self._destination = destination
        self._sent_clock = None
        self._recv_clock = None

    def which_source(self):
        '''which_source: Returns the originator of the packet

        Returns:
            The compute element which sent this packet.

        '''
        return self._source

    def which_destination(self):
        '''which_destination: Returns the destination of the packet

        Returns:
            The compute element of which this packet is intended for.

        '''
        return self._destination


    def stamp_sent(self, clock):
        self._sent_clock = clock

    def when_was_sent(self):
        return self._sent_clock

    def stamp_received(self, clock):
        self._recv_clock = clock

    def when_was_received(self):
        return self._recv_clock

class MemWritePacket(ComPacket):
    '''MemWritePacket: A packet outlining a memory write transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        address: An integer address.
        data: The contents to put at the memory address.
        clock: The clock cycle issued at this request

    Returns:
        a MemWritePacket object

    '''
    def __init__(self, source, destination, address, data):
        ComPacket.__init__(self, source, destination)

        self._address = address
        self._data = data

    def address(self):
        '''address: Returns the address for the memory write

        Returns:
            An integer

        '''
        return self._address

    def data(self):
        '''address: Returns the contents for the memory write

        Returns:
            An integer

        '''
        return self._data



class MemReadPacket(ComPacket):
    '''MemReadPacket: A packet outlining a memory read transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        address: An integer address.

    Returns:
        a MemReadPacket object

    '''
    def __init__(self, source, destination, address):
        ComPacket.__init__(self, source, destination)
        self._address = address

    def address(self):
        '''address: Returns the address for the memory write

        Returns:
            An integer

        '''
        return self._address


class DataPacket(ComPacket):
    '''DataPacket: A packet outlining a data xfer transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a DataPacket object

    '''
    def __init__(self, source, destination, data):
        ComPacket.__init__(self, source, destination)
        self._data = data

    def data(self):
        '''data: Returns the data that was meant to be xferd.

        Returns:
            An integer

        '''
        return self._data


class PEPacket(ComPacket):
    '''PEPacket: A packet outlining a computation for a PE

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, op1, op2, operation):
        ComPacket.__init__(self, source, destination)
        self._op1 = op1
        self._op2 = op2
        self._operation = operation

    def op1(self):
        '''op1: Returns the first operand

        Returns:
            A value

        '''
        return self._op1

    def op2(self):
        '''op2: Returns the second operand

        Returns:
            A value

        '''
        return self._op2

    def operation(self):
        '''operation: Returns the operation to conduct

        Returns:
            A value

        '''
        return self._operation        


class TilePacket(ComPacket):
    '''TilePacket: A packet outlining a command for the tile to dispatch

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, op1, op2, operation):
        ComPacket.__init__(self, source, destination)
        self._op1 = op1
        self._op2 = op2
        self._operation = operation

    def op1(self):
        '''op1: Returns the first operand

        Returns:
            A value

        '''
        return self._op1

    def op2(self):
        '''op2: Returns the second operand

        Returns:
            A value

        '''
        return self._op2

    def operation(self):
        '''operation: Returns the operation to conduct

        Returns:
            A value

        '''
        return self._operation        