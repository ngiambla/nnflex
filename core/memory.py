''' Memory.py: An abstraction to define memory subsystems for any compute structure.

Usage:
    Specialize this class to reflect "real-world" memory systems, such as a DRAM.

'''

from core.compackets import MemWritePacket, MemReadPacket, DataPacket


class Memory:
    ''' An abstract class that represents a memory

    Notes:
        Two main methods are provided, `_peek` and `_poke`, which read
        and write to the memory, respectively. 

    Args:
        is_external: Determines if the memory should be made external (DRAM) or internal (SRAM-ish).
        word_sz: The number of bytes to be read 
        width:  The number of words in the memory (e.g., words*word_sz bytes large)
        cycles_per_read: The numbers of cycles (estimated) required for a read.
        cycles_per_write: The number of cycles (estimated) required for a write.

    Returns:
        A "Memory" object.
    '''
    def __init__(self, system_clock_ref, interconnect, is_external = False, word_sz = 4, width = 10000):

        
        self._system_clock_ref = system_clock_ref
        self._interconnect = interconnect
        self._interconnect.add_connection(self)

        self._is_external = is_external

        # Create a "fake" memory
        self._memory = [None]*int(width)
        self._word_sz = word_sz
        self._width = width 

        self._transaction_log = list()





    def _peek(self, address: int):
        '''_peek: Reads out contents from a memory address.

        Notes:
            An address is supplied, and can possibly throw a value errors if
            (1) the address is outside of the provided range.
            (2) the contents at that address is invalid (uninitialized)

        Args:
            address: An int representing the address to read from.
            requestor_state: A requestor_state object which holds stats

        Returns:
            An int, representing the memory of the specified

        '''
        if address > self._width or address < 0:
            raise ValueError("Memory Address is out-of-bounds.")

        if self._memory[address] is None:
            raise ValueError("Reading uninitialized memory.")


        #If external memory, log this.
        if self._is_external:
            # We are using DRAMSim2
            # and the format is  <address_hex> <read/write> <Cycle_count>
            transaction = ('0x%08x' % address)+" read "+str(self._system_clock_ref.current_clock())
            self._transaction_log.append(transaction)

        return self._memory[address]


    def _poke(self, address: int, contents: int):
        '''_poke: Write contents to a memory address.

        Notes:
            An address is supplied, and can possibly throw a value errors if
            (1) the address is outside of the provided range.
            (2) the contents at that address is invalid (uninitialized)

        Args:
            address: An int representing the address to write to.
            contents: An int representing the contents to write
            requestor_state: A requestor_state object which holds stats

        Returns:
            An int, representing the memory of the specified
        '''
        if address > self._width or address < 0:
            raise ValueError("Memory Address is out-of-bounds.")

        self._memory[address] = contents


        #If external memory, log this.
        if self._is_external:
            # We are using DRAMSim2
            # and the format is  <address_hex> <read/write> <Cycle_count>
            transaction = ('0x%08x' % address)+" write "+str(self._system_clock_ref.current_clock())
            self._transaction_log.append(transaction)


    def write_transaction_log(self):
        if not self._is_external:
            return

        for transaction in self._transaction_log:
            print(transaction)

