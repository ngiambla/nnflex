'''
'''
import pytest

from core.utils import *

@pytest.mark.parametrize("int_repr", range(5000))
def test_message_router_send(int_repr):
	assert int_repr == float_to_int_repr_of_float(int_repr_of_float_to_float(int_repr))
