''' nio_mem.py: A specialization of the memory class, for use with Nick's Accelerator

'''

from enum import Enum


from core.memory import Memory
from core.messaging import Message
from core.pipeline import Stage

class NioMemory(Memory):
    ''' NioMemory: Nick's External Memory, Single Port...

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

        self._shared_fetch_pipe = MemoryStageFetch(self, message_router)

        self._pipeline_size = 2

        self._pipeline_sequence = list(range(1, self._pipeline_size))
        self._pipeline_reversed = self._pipeline_sequence[::-1]
        

        self._read_pipeline = [None for x in range(0, self._pipeline_size)]
        self._read_pipeline[0] = READStageI(self, message_router)
        for i in range(1, self._pipeline_size-1):
            self._read_pipeline[i] = MemoryFillStage()
        self._read_pipeline[self._pipeline_size-1] = READStageII(self, message_router)

        self._write_pipeline = [None for x in range(0, self._pipeline_size)]
        self._write_pipeline[0] = WriteStageI(self, message_router)
        for i in range(1, self._pipeline_size-1):
            self._write_pipeline[i] = MemoryFillStage()        
        self._write_pipeline[self._pipeline_size-1] = WriteStageII(self, message_router)

        self._stall = False
        self._num_stalls = 0


    def process(self):
        '''
        
        '''

        if self._stall:
            self._write_pipeline[-1].process()
            self._read_pipeline[-1].process()
            self._num_stalls += 1
            return 
        

        for i in self._pipeline_reversed:
            self._write_pipeline[i].accept_message(self._write_pipeline[i-1].get_message())
            self._read_pipeline[i].accept_message(self._read_pipeline[i-1].get_message())

        self._shared_fetch_pipe.process()
        message = self._shared_fetch_pipe.get_message()
        self._write_pipeline[0].accept_message(None)
        self._read_pipeline[0].accept_message(None)
        if message is not None:
            if message.mtype == Message.MemRead:
                self._read_pipeline[0].accept_message(message)
            elif message.mtype == Message.MemWrite:
                self._write_pipeline[0].accept_message(message)


        for stage in self._write_pipeline:
            stage.process()

        for stage in self._read_pipeline:
            stage.process()

    def number_of_stalled_cycles(self):
        return self._num_stalls

    def stall(self):
        self._stall = True


    def is_stalled(self):
        return self._stall

    def continue_processing(self):
        self._stall = False


class MemoryStageFetch(Stage):
    def __init__(self, nio_memory, router):
        Stage.__init__(self)
        self._nio_memory = nio_memory
        self._router = router

    def process(self):
        self._message = self._router.fetch(self._nio_memory)

class MemoryFillStage(Stage):
    def __init__(self):
        Stage.__init__(self)

    def process(self):
        pass

class WriteStageI(Stage):
    def __init__(self, nio_memory, router):
        Stage.__init__(self)
        self._nio_memory = nio_memory
        self._router = router

    def process(self):
        if self._message is None:
            return        
        destination = self._message.source     
        message_id =  self._message.message_id
        seq_num = self._message.seq_num
        address = self._message.addr
        content = self._message.content
        self._nio_memory._poke(address, content)
        self._message = Message(self._nio_memory, destination, Message.MemWriteDone, message_id, seq_num)


class WriteStageII(Stage):
    def __init__(self, nio_memory, router):
        Stage.__init__(self)
        self._nio_memory = nio_memory
        self._router = router

    def process(self):
        if self._message is None:
            return
        self._nio_memory.continue_processing()
        if not self._router.send(self._message):
            self._message = None
            self._nio_memory.stall()


class READStageI(Stage):
    def __init__(self, nio_memory, router):
        Stage.__init__(self)
        self._nio_memory = nio_memory
        self._router = router

    def process(self):
        if self._message is None:
            return          

        destination = self._message.source
        message_id = self._message.message_id
        seq_num = self._message.seq_num            
        address = self._message.addr
        content = self._nio_memory._peek(address)
        attributes = {
            "addr" : address,
            "content" : content
        }
        self._message = Message(self._nio_memory, destination,  Message.MemReadDone, message_id, seq_num, attributes = attributes)

class READStageII(Stage):
    def __init__(self, nio_memory, router):
        Stage.__init__(self)
        self._nio_memory = nio_memory
        self._router = router

    def process(self):
        if self._message is None:
            return
        
        if not self._nio_memory.is_stalled():
            self._nio_memory.continue_processing()
        if not self._router.send(self._message):
            self._message = None
            self._nio_memory.stall()
