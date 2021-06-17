''' message.py: Messages to be sent between compute elements

'''

class Message:
    '''Message: The Base Class that all Messages should inherit from

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id

    Returns:
        a Message object

    '''
    def __init__(self, source, destination, message_id = None, seq_num = None):
        self._source = source
        self._destination = destination
        self._sent_clock = None
        self._recv_clock = None

        # This can be used to refer to a parent packet
        self._message_id = message_id
        # Ordering of a multi-part response
        self._seq_num = seq_num

    def get_message_id(self):
        '''
        get_message_id: Returns the identifier of this message

        Returns:
            An identifier of this message (can be a string, int, etc)
        '''
        return self._message_id

    def get_seq_num(self):
        '''
        get_seq_num: For a multi-part message, this identifies the order.

        Returns:
            The number representing which "part" of the multi-part message this was apart of.
        '''        
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


    def stamp_time_sent(self, clock):
        ''' stamp_time_sent: 
            
        '''
        self._sent_clock = clock

    def when_was_sent(self):
        return self._sent_clock

    def stamp_time_received(self, clock):
        self._recv_clock = clock

    def when_was_received(self):
        return self._recv_clock

class MemoryWriteRequest(Message):
    '''MemoryWriteReq: A Message representing a memory write transaction

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id
        address: An integer address.
        data: The contents to put at the memory address.

    Returns:
        a MemoryWriteReq object

    '''
    def __init__(self, source, destination, message_id, seq_num, address, data):
        Message.__init__(self, source, destination, message_id, seq_num)

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


class MemoryWriteComplete(Message):
    '''MemoryWriteComplete: A Message which indicates the completion of a memory write transaction

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id

    Returns:
        a MemoryWriteComplete object

    '''
    def __init__(self, source, destination, message_id, seq_num):
        Message.__init__(self, source, destination, message_id, seq_num)   



class MemoryReadRequest(Message):
    '''MemReadPacket: A Message representing a request for a memory read transaction

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id        
        address: An integer address.

    Returns:
        a MemoryReadRequest object

    '''
    def __init__(self, source, destination, message_id, seq_num, address):
        Message.__init__(self, source, destination, message_id, seq_num)
        self._address = address

    def address(self):
        '''address: Returns the address for the memory write

        Returns:
            An integer

        '''
        return self._address


class MemoryReadComplete(Message):
    '''MemoryReadComplete: A Message representing the completion of a memory read

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id 
        address: An integer address.
        content: The contents at the integer address

    Returns:
        a MemReadPacket object

    '''
    def __init__(self, source, destination, message_id, seq_num, address, content):
        Message.__init__(self, source, destination, message_id, seq_num)
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


class PECommand(Message):
    '''PECommand: A Message representing a command for a PE

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id
        op1: The first operand (left-hand side)
        op2: The second operand (right-hand side)
        operation: The operation for the PE to conduct.

    Returns:
        a PECommand object

    '''
    def __init__(self, source, destination, message_id, seq_num, op1, op2, operation):
        Message.__init__(self, source, destination, message_id, seq_num)
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

class PEResponse(Message):
    '''PEResponse: A Message returning the response from a PE command

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id
        data: Data to be transferred

    Returns:
        a PEResponse object

    '''
    def __init__(self, source, destination, message_id, seq_num, result):
        Message.__init__(self, source, destination, message_id, seq_num)
        self._result = result

    def result(self):
        '''result: Returns the result from the PE-command

        Returns:
            A value

        '''
        return self._result

class TileCommand(Message):
    '''TileCommand: A Message representing a command for the tile to dispatch

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id
        op1_addr: The address (memory) of the first operand (left-hand side)
        op2_addr: The address (memory) of the second operand (right-hand side)
        res_addr: The address (memory) of the where to store the result.
        operation: The operation for the PE to conduct.

    Returns:
        a TileCommand object

    '''
    def __init__(self, source, destination, message_id, op1_addr, op2_addr, res_addr, operation):
        Message.__init__(self, source, destination, message_id)
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


class TileCommandComplete(Message):
    '''TileCommandComplete: A Message indicating the completion of a TileCommand

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.

    Returns:
        a TileCommandComplete object

    '''
    def __init__(self, source, destination, message_id):
        Message.__init__(self, source, destination, message_id)
