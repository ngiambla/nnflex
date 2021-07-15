''' test_allocator.py

Tests the allocator implementation.
Note:
	The allocator used is a Bitmap Allocation Method.
	To find more details about it: 
		(1) https://github.com/ngiambla/libmem/blob/master/allocators/libbitmem.c
		(2) https://tspace.library.utoronto.ca/bitstream/1807/101133/3/Giamblanco_Nicholas_Vincent_202006_MAS_thesis.pdf
'''
import pytest

from core.allocator import BitAlloc



@pytest.mark.parametrize("mem_size", [None, 0, -1, 34])
@pytest.mark.parametrize("req_size", [None, 0, -1.0, 33])
def test_allocator_instantiate_invalid(mem_size, req_size):
	''' checks if we catch invalid instantiations of the allocator.
	'''
	result = False
	try:
		BitAlloc(mem_size, req_size)
	except ValueError as VE:
		result = True

	assert result


@pytest.mark.parametrize("mem_size", [100,400,1000])
@pytest.mark.parametrize("req_size", [4])
@pytest.mark.parametrize("nbytes",   [4, 8, 16, 17, 32])
def test_allocator_normal_once(mem_size, req_size, nbytes):
	''' checks if a normal allocation is handled correctly.

	We expect the first and only allocation to return an address of 0, 
	regardless of the size.

	'''
	allocator = BitAlloc(mem_size, req_size)
	assert allocator.alloc(nbytes) == 0




@pytest.mark.parametrize("mem_size", [100])
@pytest.mark.parametrize("req_size", [4])
@pytest.mark.parametrize("nbytes",   [4, 8, 16, 32])
def test_allocator_normal_successive(mem_size, req_size, nbytes):
	''' inspects normal successive allocation behaviour.
	'''
	allocator = BitAlloc(mem_size, req_size)
	for i in range (0, 4):
		assert allocator.alloc(nbytes) == nbytes*i


def test_allocator_alloc_free_alloc():
	''' Validates the allocator can free memory correctly.
	'''
	allocator = BitAlloc(100, 4)
	addr = None
	for i in range (0, 4):
		addr_tmp = allocator.alloc(32)
		if i == 2:
			addr = addr_tmp

	allocator.free(addr)
	assert allocator.show_map() == "FFFF00FF0000000000000000"
	allocator.alloc(4)
	assert allocator.show_map() == "FFFF80FF0000000000000000"


def test_allocator_alloc_free_alloc_misaligned():
	allocator = BitAlloc(100, 4)
	addr = None
	for i in range (0, 4):
		addr_tmp = allocator.alloc(31)
		if i == 2:
			addr = addr_tmp

	allocator.free(addr)
	assert allocator.show_map() == "FFFF00FF0000000000000000"
	allocator.alloc(4)
	assert allocator.show_map() == "FFFF80FF0000000000000000"


def test_allocator_alloc_free_alloc_spill_ordered():
	allocator = BitAlloc(100, 4)
	addr0 = None
	addr2 = None
	for i in range (0, 4):
		addr_tmp = allocator.alloc(31)
		if i == 0:
			addr0 = addr_tmp
		if i == 2:
			addr2 = addr_tmp

	allocator.free(addr0)
	allocator.free(addr2)
	assert allocator.show_map() == "00FF00FF0000000000000000"
	allocator.alloc(4)
	assert allocator.show_map() == "80FF00FF0000000000000000"

def test_allocator_alloc_free_alloc_spill_unordered():
	allocator = BitAlloc(100, 4)
	addr0 = None
	addr2 = None
	for i in range (0, 4):
		addr_tmp = allocator.alloc(31)
		if i == 0:
			addr0 = addr_tmp
		if i == 2:
			addr2 = addr_tmp

	allocator.free(addr2)
	allocator.free(addr0)
	assert allocator.show_map() == "00FF00FF0000000000000000"
	addr = allocator.alloc(20)
	assert allocator.show_map() == "F8FF00FF0000000000000000"
	allocator.free(addr)
	assert allocator.show_map() == "00FF00FF0000000000000000"


def test_allocator_oom():
	result = False
	allocator = BitAlloc(4,4)

	if allocator.alloc(8) is None:
		result = True

	assert result

