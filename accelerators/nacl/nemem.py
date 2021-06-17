''' nemem.py: A specialization of the memory class, for use with Nick's Accelerator

'''

from enum import Enum


from core.memory import Memory
from core.message import MemoryWriteRequest, MemoryWriteComplete, MemoryReadRequest, MemoryReadComplete


class ReadStage(Enum):
    READ_I = 1
    READ_II = 2
    READ_DONE = 3
    READ_SEND = 4
    WAIT = 5

class WriteStage(Enum):
    WRITE_I = 1
    WRITE_II = 2
    WRITE_DONE = 3
    WRITE_SEND = 4
    WAIT = 5


class NEMemory(Memory):
    ''' NEMemory: Nick's External Memory, Single Port...

    Args:
         system_clock_ref: The reference to the system clock.
        message_router: The router to handle communication transactions.
        message_queue_size: The number of additional Messages for the router to store when busy (default: 1)
        log_transactions: If we wish to store this to a 
        word_byte_size: The number of bytes per memory cell.
        width:  The number of words in the memory (e.g., words*word_byte_size bytes large)
           
    Returns:
        A "Memory" object.
    '''
    def __init__(self, system_clock_ref, message_router, word_byte_size = 4, width = 10000):

        Memory.__init__(self, system_clock_ref, message_router, 1, True, word_byte_size, width)

        self._current_read_message = None
        self._current_read_stage = ReadStage.WAIT
        self._next_read_stage = ReadStage.WAIT
        self._read_ackd_message = None


        self._current_write_message = None
        self._current_write_stage = WriteStage.WAIT
        self._next_write_stage = WriteStage.WAIT
        self._write_ackd_message = None

        # To handle more than 1 message at a time.
        self._message_buffer = list()
        self._message_size = 1

    def process(self):

        self._load_messages_from_message_router()
        self._process_write()
        self._process_read()

    def _process_write(self):
        self._current_write_stage = self._next_write_stage

        if self._current_write_stage == WriteStage.WRITE_I:
            self._next_write_stage = WriteStage.WRITE_II

        if self._current_write_stage == WriteStage.WRITE_II:
            self._next_write_stage = WriteStage.WRITE_DONE

        if self._current_write_stage == WriteStage.WRITE_DONE:
            destination = self._current_write_message.source_device()            
            address = self._current_write_message.address()
            content = self._current_write_message.data()
            self._poke(address, content)
            self._write_ackd_message = MemoryWriteComplete(self, destination, self._current_write_message.get_message_id(), self._current_write_message.get_seq_num())
            self._next_write_stage = WriteStage.WRITE_SEND

        if self._current_write_stage == WriteStage.WRITE_SEND:
            self._next_write_stage = WriteStage.WRITE_SEND
            if self._message_router.send(self._write_ackd_message):
                self._next_write_stage = WriteStage.WAIT

        if self._current_write_stage == WriteStage.WAIT:
            self._next_write_stage = WriteStage.WAIT
            messages_to_remove = list()
            for i in range(len(self._message_buffer)):
                message = self._message_buffer[i]
                if isinstance(message, MemoryWriteRequest):
                    self._current_write_message = message
                    messages_to_remove.append(i)
                    self._next_write_stage = WriteStage.WRITE_I
                    break
            for message_idx in messages_to_remove:
                self._message_buffer.pop(message_idx)



    def _process_read(self):
        self._current_read_stage = self._next_read_stage

        if self._current_read_stage == ReadStage.READ_I:
            self._next_read_stage = ReadStage.READ_II

        if self._current_read_stage == ReadStage.READ_II:
            self._next_read_stage = ReadStage.READ_DONE

        if self._current_read_stage == ReadStage.READ_DONE:
            self._next_read_stage = ReadStage.READ_SEND
            destination = self._current_read_message.source_device()
            address = self._current_read_message.address()
            content = self._peek(address)
            self._read_ackd_message = MemoryReadComplete(self, destination, self._current_read_message.get_message_id(), self._current_read_message.get_seq_num(), address,content)

        if self._current_read_stage == ReadStage.READ_SEND:
            self._next_read_stage = ReadStage.READ_SEND
            if self._message_router.send(self._read_ackd_message):
                self._next_read_stage = ReadStage.WAIT

        if self._current_read_stage == ReadStage.WAIT:
            self._next_read_stage = ReadStage.WAIT
            messages_to_remove = list()
            for i in range(len(self._message_buffer)):
                message = self._message_buffer[i]
                if isinstance(message, MemoryReadRequest):
                    self._current_read_message = message
                    messages_to_remove.append(i)
                    self._next_read_stage = ReadStage.READ_I
                    break

            for message_idx in messages_to_remove:
                self._message_buffer.pop(message_idx)


    def _load_messages_from_message_router(self):
        while len(self._message_buffer) < self._message_size:
            message = self._message_router.fetch(self)
            if message is None:
                return
            self._message_buffer.append(message)

