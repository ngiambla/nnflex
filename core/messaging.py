''' messaging.py: Messages to be sent between devices

'''

from core.defines import Operator

class Message:
    '''Message: Representings the information for distributing a set
    of commands/information to a particular device

    Args:
        source: The compute element which is sending the message
        destination: The compute element which is to receive the message.
        message_id: An identifier to classify what message sequence this belongs to.
        seq_num: An ordered response associated with message_id

    Returns:
        a Message object

    '''

    MemWrite = 0
    MemWriteDone = 1
    MemRead = 2
    MemReadDone = 3
    PECmd = 4
    PEDone = 5
    TileCmd = 6
    TileDone = 7


    def __init__(self, source, destination, mtype, message_id = None, seq_num = None, attributes = None):
        self.source = source
        self.destination = destination
        self.sent_clock = None
        self.recv_clock = None

        # This can be used to refer to a parent packet
        self.message_id = message_id
        # Ordering of a multi-part response
        self.seq_num = seq_num

        self.mtype = mtype

        self._supported_types = {self.MemWrite, self.MemWriteDone, self.MemRead, self.MemReadDone, self.PECmd, self.PEDone, self.TileCmd, self.TileDone}

        # If a keyword argument dictionary was supplied, set this object's attributes. 
        if attributes is not None:
            for k, v in attributes.items():
                setattr(self, k, v)

        if self.mtype is None:
            raise ValueError("Cannot create a message with type None.")

        if not isinstance(self.mtype, int):
            raise ValueError("The message type needs to be an integer.")

        if not self.mtype in self._supported_types:
            raise ValueError("Please choose a supported mtype: "+str(self._supported_types))

        if self.mtype == self.MemWrite:
            assert hasattr(self, "addr")
            assert hasattr(self, "content")

        elif self.mtype == self.MemRead:
            assert hasattr(self, "addr")

        elif self.mtype == self.MemReadDone:
            assert hasattr(self, "addr")
            assert hasattr(self, "content")

        elif self.mtype == self.PECmd:
            self.num_operands = 2
            if hasattr(self, "op3"):
                self.num_operands += 1
            assert hasattr(self, "operation")
            assert hasattr(self, "dtype")

        elif self.mtype == self.PEDone:
            assert hasattr(self, "result")

        elif self.mtype == self.TileCmd:

            assert hasattr(self, "res_addr")
            assert hasattr(self, "operation")
            assert hasattr(self, "dtype")


            if self.operation == Operator.DOT:
                assert hasattr(self, "row_addrs")
                assert hasattr(self, "col_addrs")
                if not hasattr(self, "bias"):
                    self.bias = None

            elif self.operation in {Operator.ADD, Operator.MUL, Operator.SUB, Operator.DIV, Operator.MAX}:
                if not hasattr(self, "op1_addr"):
                    assert hasattr(self, "op1")

                if not hasattr(self, "op2_addr"):
                    assert hasattr(self, "op2")
