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
        packet_id: An identifier to classify what packet sequence this belongs to.
        seq_num: An ordered response associated with packet_id

    Returns:
        a ComPacket object

    '''
    def __init__(self, source, destination, packet_id = None, seq_num = None):
        self._source = source
        self._destination = destination
        self._sent_clock = None
        self._recv_clock = None

        # This can be used to refer to a parent packet
        self._packet_id = packet_id
        # Ordering of a multi-part response
        self._seq_num = seq_num

    def get_packet_id(self):
        return self._packet_id

    def get_seq_num(self):
        return self._seq_num



    def source_device(self):
        '''source_device: Returns the originator of the packet

        Returns:
            The compute element which sent this packet.

        '''
        return self._source

    def destination_device(self):
        '''destination_device: Returns the destination of the packet

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
    def __init__(self, source, destination, packet_id, seq_num, address, data):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)

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


class MemWriteAckPacket(ComPacket):
    '''MemWriteAckPacket: A packet acknowledging a memory write transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        packet_id: An integer address.

    Returns:
        a MemWriteAckPacket object

    '''
    def __init__(self, source, destination, packet_id, seq_num):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)   



class MemReadPacket(ComPacket):
    '''MemReadPacket: A packet outlining a memory read transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        address: An integer address.

    Returns:
        a MemReadPacket object

    '''
    def __init__(self, source, destination, packet_id, seq_num, address):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)
        self._address = address

    def address(self):
        '''address: Returns the address for the memory write

        Returns:
            An integer

        '''
        return self._address


class MemReadAckPacket(ComPacket):
    '''MemReadPacket: A packet outlining a memory read transaction

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        address: An integer address.

    Returns:
        a MemReadPacket object

    '''
    def __init__(self, source, destination, packet_id, seq_num, address, content):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)
        self._address = address
        self._content = content

    def address(self):
        '''address: Returns the address for the memory read

        Returns:
            An integer

        '''
        return self._address

    def content(self):
        '''content: Returns the contents at that memory address

        Returns:
            An integer

        '''
        return self._content


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


class PEReqPacket(ComPacket):
    '''PEPacket: A packet outlining a computation for a PE

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, packet_id, seq_num, op1, op2, operation):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)
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

class PERespPacket(ComPacket):
    '''PEResponsePacket: A packet returning the response of a PE calculation

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, packet_id, seq_num, result):
        ComPacket.__init__(self, source, destination, packet_id, seq_num)
        self._result = result

    def result(self):
        '''op1: Returns the first operand

        Returns:
            A value

        '''
        return self._result

class TileReqPacket(ComPacket):
    '''TilePacket: A packet outlining a command for the tile to dispatch

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, packet_id, op1_addr, op2_addr, res_addr, operation):
        ComPacket.__init__(self, source, destination, packet_id)
        self._op1_addr = op1_addr
        self._op2_addr = op2_addr
        self._res_addr = res_addr 
        self._operation = operation

    def op1_addr(self):
        '''address_op1: Returns the first operand

        Returns:
            A value

        '''
        return self._op1_addr

    def op2_addr(self):
        '''address_op2: Returns the second operand

        Returns:
            A value

        '''
        return self._op2_addr

    def res_addr(self):
        '''res_addr: The memory address to write the result to.

        Returns:
            integer representing the address

        '''
        return self._res_addr

    def operation(self):
        '''operation: Returns the operation to conduct

        Returns:
            A value

        '''
        return self._operation


class TileRespPacket(ComPacket):
    '''TilePacket: A packet outlining a command for the tile to dispatch

    Args:
        source: The compute element which is sending the packet
        destination: The compute element which is to receive the packet.
        data: Data to be transferred

    Returns:
        a PEPacket object

    '''
    def __init__(self, source, destination, packet_id):
        ComPacket.__init__(self, source, destination, packet_id)
