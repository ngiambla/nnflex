''' nnflex.py: The main hook into the nnflex framework.

Notes:



'''
import argparse

from accelerators.nacl.nacl import NaCl, NaClSupportLayer
from translator.onnx2flex import ONNX2Flex
import numpy as np


class Tensor():
	def __init__(self, data_list):
		self.data = data_list



def main():
	# parser = argparse.ArgumentParser(description="Flexible Neural Network Accelerator Simulation Engine")
	# parser.add_argument('-m','--model', help='Neural Network in ONNX', required=True)
	# parser.add_argument('-c','--config', help='Accelerator Configuration', required=True)	
	# parser.parse_args()

	onnx2flex = ONNX2Flex("examples/mnist.onnx")
	onnx2flex.translate()

	# local_nacl = NaCl(num_tile_rows=10, num_tile_cols=10)

	# in_acts = np.asarray(list(range(1, 1000)))
	# weights = np.asarray(list(range(1, 1000)))
	# outputs = np.asarray(list(range(1, 1000)))
	# local_nacl.forward("elemwiseadd", in_acts, weights, outputs)
	# print(outputs)



if __name__ == "__main__":
	main()