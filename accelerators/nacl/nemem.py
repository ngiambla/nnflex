''' nemem.py: A specialization of the memory class, for use with Nick's Accelerator

'''

from enum import Enum


from core.memory import Memory
from core.compackets import MemWritePacket, MemWriteAckPacket, MemReadPacket, MemReadAckPacket


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
        is_external: Determines if the memory should be made external (DRAM) or internal (SRAM-ish).
        word_sz: The number of bytes to be read 
        width:  The number of words in the memory (e.g., words*word_sz bytes large)
        cycles_per_read: The numbers of cycles (estimated) required for a read.
        cycles_per_write: The number of cycles (estimated) required for a write.

    Returns:
        A "Memory" object.
    '''
    def __init__(self, system_clock_ref, interconnect, word_sz = 4, width = 10000):

        Memory.__init__(self, system_clock_ref, interconnect, True, word_sz, width)

        self._current_read_packet = None
        self._current_read_stage = ReadStage.WAIT
        self._next_read_stage = ReadStage.WAIT
        self._read_ackd_packet = None


        self._current_write_packet = None
        self._current_write_stage = WriteStage.WAIT
        self._next_write_stage = WriteStage.WAIT
        self._write_ackd_packet = None

        # To handle more than 1 packet at a time.
        self._packet_buffer = list()
        self._packet_size = 1

    def process(self):

        self._load_packets_from_interconnect()
        self._process_write()
        self._process_read()

    def _process_write(self):
        self._current_write_stage = self._next_write_stage

        if self._current_write_stage == WriteStage.WRITE_I:
            self._next_write_stage = WriteStage.WRITE_II

        if self._current_write_stage == WriteStage.WRITE_II:
            self._next_write_stage = WriteStage.WRITE_DONE

        if self._current_write_stage == WriteStage.WRITE_DONE:
            destination = self._current_write_packet.source_device()            
            address = self._current_write_packet.address()
            content = self._current_write_packet.data()
            self._poke(address, content)
            self._write_ackd_packet = MemWriteAckPacket(self, destination, self._current_write_packet.get_packet_id(), self._current_write_packet.get_seq_num())
            self._next_write_stage = WriteStage.WRITE_SEND

        if self._current_write_stage == WriteStage.WRITE_SEND:
            self._next_write_stage = WriteStage.WRITE_SEND
            if self._interconnect.send(self._write_ackd_packet):
                self._next_write_stage = WriteStage.WAIT

        if self._current_write_stage == WriteStage.WAIT:
            self._next_write_stage = WriteStage.WAIT
            packets_to_remove = list()
            for i in range(len(self._packet_buffer)):
                packet = self._packet_buffer[i]
                if isinstance(packet, MemWritePacket):
                    self._current_write_packet = packet
                    packets_to_remove.append(i)
                    self._next_write_stage = WriteStage.WRITE_I
                    break
            for packet_idx in packets_to_remove:
                self._packet_buffer.pop(packet_idx)



    def _process_read(self):
        self._current_read_stage = self._next_read_stage

        if self._current_read_stage == ReadStage.READ_I:
            self._next_read_stage = ReadStage.READ_II

        if self._current_read_stage == ReadStage.READ_II:
            self._next_read_stage = ReadStage.READ_DONE

        if self._current_read_stage == ReadStage.READ_DONE:
            self._next_read_stage = ReadStage.READ_SEND
            destination = self._current_read_packet.source_device()
            address = self._current_read_packet.address()
            content = self._peek(address)
            self._read_ackd_packet = MemReadAckPacket(self, destination, self._current_read_packet.get_packet_id(), self._current_read_packet.get_seq_num(), address,content)

        if self._current_read_stage == ReadStage.READ_SEND:
            self._next_read_stage = ReadStage.READ_SEND
            if self._interconnect.send(self._read_ackd_packet):
                self._next_read_stage = ReadStage.WAIT

        if self._current_read_stage == ReadStage.WAIT:
            self._next_read_stage = ReadStage.WAIT
            packets_to_remove = list()
            for i in range(len(self._packet_buffer)):
                packet = self._packet_buffer[i]
                if isinstance(packet, MemReadPacket):
                    self._current_read_packet = packet
                    packets_to_remove.append(i)
                    self._next_read_stage = ReadStage.READ_I
                    break

            for packet_idx in packets_to_remove:
                self._packet_buffer.pop(packet_idx)


    def _load_packets_from_interconnect(self):
        while len(self._packet_buffer) < self._packet_size:
            packet = self._interconnect.get_packet(self)
            if packet is None:
                return
            self._packet_buffer.append(packet)

