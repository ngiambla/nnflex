''' cache.py

Implements a very basic cache, with NO write-back (this cache should ONLY be used for caching inputs), 
and does not implement a replacement policy (e.g., LRU)

NOTE:
	This should be improved. A true cache-block should be designed.

'''


class Cache:

	def __init__(self, num_entries):
		self._num_entries = num_entries
		self._cache = [{None: None}]*num_entries

	def lookup(self, address):
		cache_idx = address%self._num_entries
		if address not in self._cache[cache_idx]:
			return None
		return self._cache[cache_idx][address]


	def install(self, address, contents):
		cache_idx = address%self._num_entries
		self._cache[cache_idx] = dict()
		self._cache[cache_idx][address] = contents


	def clear(self):
		self._cache = [{None: None}]*self._num_entries
