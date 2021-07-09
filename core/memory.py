''' memory.py: An abstraction to define memory subsystems for any compute structure.

Usage:
    Specialize this class to reflect "real-world" memory systems, such as a DRAM.

'''

import subprocess
import os

from core.device import Device


class Memory(Device):
    ''' An abstract class that represents a memory

    Notes:
        Two main methods are provided, `_peek` and `_poke`, which read
        and write to the memory, respectively. 

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

    def __init__(self, system_clock_ref, message_router, message_queue_size=1, log_transactions=False, word_byte_size=4, width=10000):
        Device.__init__(self, system_clock_ref, message_router, message_queue_size)

        self._log_transacations = log_transactions

        if width < 1:
            raise ValueError("The width of the Memory must be a positive integer.")

        if word_byte_size < 1:
            raise ValueError("The word size (in bytes) must be a positive integer.")

        # Create a "fake" memory
        self._memory = [None]*int(width)
        self._word_byte_size = word_byte_size
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
        if not isinstance(address, int):
            raise ValueError("Memory Address must be an integer.")

        if address >= self._width or address < 0:
            raise ValueError("Memory Address is out-of-bounds.")

        if self._memory[address] is None:
            raise ValueError("Reading uninitialized memory.")

        # If _log_transacations is True, log this.
        if self._log_transacations:
            # We are using DRAMSim2
            # and the format is  <address_hex> <read/write> <Cycle_count>
            transaction = ('0x%08x' % address)+" read " + \
                str(self._system_clock_ref.current_clock())
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
        if not isinstance(address, int):
            raise ValueError("Memory Address must be an integer.")

        if not isinstance(contents, int):
            raise ValueError("Contents must be an integer.")

        if address >= self._width or address < 0:
            raise ValueError("Memory Address is out-of-bounds.")

        self._memory[address] = contents

        # If _log_transacations is True, log this.
        if self._log_transacations:
            # We are using DRAMSim2
            # and the format is  <address_hex> <read/write> <Cycle_count>
            transaction = ('0x%08x' % address)+" write " + \
                str(self._system_clock_ref.current_clock())
            self._transaction_log.append(transaction)

    def write_transaction_log(self):
        if not self._log_transacations:
            return

        with open("misc_transactions.trc", "w+") as f:
            for transaction in self._transaction_log:
                f.write(transaction+"\n")

        # TODO: Look into an automatic run and parse of this.
        #subprocess.run(["dramsim2/./DRAMSim","-t misc_transactions.trc", "-s dramsim2/system.ini.example", "-d dramsim2/ini/DDR3_micron_64M_8B_x4_sg15.ini"])

    def size(self):
        return self._width*self._word_byte_size


    def process(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator-PE-Specification")


    def collect_statistics(self):
        '''
        '''
        raise NotImplementedError("Please specialize according to the Accelerator Specification")

