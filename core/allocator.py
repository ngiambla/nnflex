''' allocator.py

Outlines a Bitmap Allocator, with emphasis on efficiency.

Heavily influenced by:
(1) https://github.com/ngiambla/libmem/blob/master/allocators/libbitmem.c
(2) https://tspace.library.utoronto.ca/bitstream/1807/101133/3/Giamblanco_Nicholas_Vincent_202006_MAS_thesis.pdf

Author: Nicholas V. Giamblanco
Date: June 16, 2021

'''
def num_high_bits(n):
  n = (n & 0x5555555555555555) + ((n & 0xAAAAAAAAAAAAAAAA) >> 1)
  n = (n & 0x3333333333333333) + ((n & 0xCCCCCCCCCCCCCCCC) >> 2)
  n = (n & 0x0F0F0F0F0F0F0F0F) + ((n & 0xF0F0F0F0F0F0F0F0) >> 4)
  n = (n & 0x00FF00FF00FF00FF) + ((n & 0xFF00FF00FF00FF00) >> 8)
  n = (n & 0x0000FFFF0000FFFF) + ((n & 0xFFFF0000FFFF0000) >> 16)
  n = (n & 0x00000000FFFFFFFF) + ((n & 0xFFFFFFFF00000000) >> 32)
  return n

class BitAlloc():
    ''' BitAlloc: A Memory Allocator:
        
        A bitmap dynamic memory allocator employs a bit-vector, Vb = {b0, b1, ...bn}, to maintain state on
        memory reservations within a memory device (i.e., heap). Each bit "bi" in this bit-vector maps to X bytes at a unique location
        in the heap.

    '''
    def __init__(self, memory_size_in_bytes, min_request_size = 4):

        if not isinstance(memory_size_in_bytes, int) or memory_size_in_bytes < 1:
            raise ValueError("memory_size_in_bytes must be a postive integer.")

        if not isinstance(min_request_size, int) or min_request_size < 1:
            raise ValueError("min_request_size must be a postive integer.")
        
        if memory_size_in_bytes % min_request_size != 0:
            raise ValueError("memory_size_in_bytes must be divisible by min_request_size")

        self._arena_size  = memory_size_in_bytes # Number of bytes available.

        # factor: 
        #     1. Each bit represents this amount of bytes (default: 4)
        #     2. Must be a power of 2.
        self._factor      = int(min_request_size)
        if num_high_bits(self._factor) != 1:
            raise ValueError("The factor must be a power of 2.")

        # factorless1:
        #     Since self._factor is a power of 2, we can use factor-1 as a mask.
        self._factorless1 = self._factor -1

        # shift_factor 
        # The divisor will be translated into a shift amount.
        self._shift_factor = self._factor.bit_length() -1

        self._blocks = self._arena_size
        self._bits_per_block = 32
        self._mapblocks = self._blocks//self._bits_per_block

        # This represents where bits are set.
        self._bitmap = [0]*self._mapblocks
        # This represents 
        self._bit_alloc_size_map = dict()


    def show_map(self):
        '''
         Displays the bitmap as a string.
        '''
        bitmap_string = ""
        for cell in self._bitmap:
            bitmap_string += '{0:08X}'.format(cell)
        return bitmap_string


    def alloc(self, num_bytes):
        ''' alloc: Requests an allocation be made, thereby reserving memory.
        
        Args:
            num_bytes: The number of bytes to reserve

        Returns:
            An integer representing the start of the allocated memory region
                OR
            None (indicating the allocation failed)
        '''

        if not isinstance(num_bytes, int) or num_bytes <= 0:
            raise ValueError("num_bytes must be a positive integer")

        current_map = None
        cur_map_idx = None

        # Force requested bytes to be at least self._factor.
        nbytes = self._factor if num_bytes < self._factor else num_bytes

        # Begin Searching the bitmap.

        # 1. Compute if we are not within a boundary of self._factor
        mod_res = nbytes&(self._factorless1);

        # 2. If we wrap, add the extra FACTOR bytes to the div of nbytes.
        num_required_bits = (nbytes - mod_res) >> self._shift_factor
        if mod_res > 0:
            num_required_bits += 1

        bits_acquired       = 0
        bitmap_start_bit    = 0
        bitmap_end_bit      = 0
        OOM                 = True

        # 3. Searching for free space within the bitmap.
        for i in range(self._mapblocks):
            current_map = self._bitmap[i] & 0xFFFFFFFF
            for j in range((self._bits_per_block-1), -1, -1):
                bits_acquired = (bits_acquired+1) if (current_map&(1<<j) == 0) else 0
                bitmap_end_bit+=1

                if bits_acquired == num_required_bits:
                    bitmap_start_bit = bitmap_end_bit - num_required_bits;
                    OOM = False
                    break

            if not OOM:
                break

        if OOM:
            return None

        real_bit_mod_res = bitmap_start_bit&(0x1F)
        map_index = (bitmap_start_bit - real_bit_mod_res)>>6
        real_bit_mod_res = self._bits_per_block - 1 - real_bit_mod_res
        addr = (bitmap_start_bit << self._shift_factor);
        self._bit_alloc_size_map[bitmap_start_bit] = num_required_bits


        bits_acquired = 0
        all_bits_set = False
        for i in range(map_index, self._mapblocks):
            current_map = self._bitmap[i] & 0xFFFFFFFF
            for j in range(real_bit_mod_res, -1, -1):
                current_map = current_map | (1 << j)
                bits_acquired += 1

                if bits_acquired == num_required_bits:
                    self._bitmap[i] = current_map
                    all_bits_set = True
                    break

            if all_bits_set:
                break

            self._bitmap[i] = current_map
            real_bit_mod_res = (self._bits_per_block-1)

        return addr

    def free(self, addr):
        ''' free: Releases the reservation of memory beginning at said address

        Args:
            addr: The number of bytes to reserve

        '''

        if not isinstance(addr, int) or addr < 0:
            raise ValueError("addr must be a positive integer")

        bitmap_start_bit = addr >> self._shift_factor
        real_bit_mod_res = bitmap_start_bit&(0x1F)
        map_index = (bitmap_start_bit - real_bit_mod_res) >> 6
        
        real_bit_mod_res = self._bits_per_block - 1 - real_bit_mod_res
        if bitmap_start_bit not in self._bit_alloc_size_map:
            raise ValueError("Address was never part of an allocation")
        bits_to_free = self._bit_alloc_size_map[bitmap_start_bit]

        for i in range(map_index, self._mapblocks):
            current_map = self._bitmap[i] & 0xFFFFFFFF
            for j in range(real_bit_mod_res, -1, -1):
                mask = 0xFFFFFFFF ^ 1<<j

                current_map = current_map & mask
                bits_to_free -= 1
                if bits_to_free == 0:
                    self._bitmap[i] = current_map
                    return
            real_bit_mod_res = (self._bits_per_block-1)
            self._bitmap[i] = current_map

        del self._bit_alloc_size_map[bitmap_start_bit]