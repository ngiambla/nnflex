''' nnflex.py: The main hook into the nnflex framework.

Notes:



'''
import argparse

from accelerators import Nio
from translator.onnx2flex import ONNX2Flex
import numpy as np


class Tensor():
	def __init__(self, data_list):
		self.data = data_list



def main():
	parser = argparse.ArgumentParser(description="Flexible Neural Network Accelerator Simulation Engine")
	parser.add_argument('-m','--model', help='Neural Network in ONNX', required=True)
	# parser.add_argument('-c','--config', help='Accelerator Configuration', required=True)	
	args = parser.parse_args()

	onnx2flex = ONNX2Flex(args.model)
	onnx2flex.translate()

	nio_impl = Nio(num_tile_rows=10, num_tile_cols=10)

	layer = onnx2flex.next_layer()
	while layer is not None:
		nio_impl.forward(layer)
		layer = onnx2flex.next_layer()



if __name__ == "__main__":
	main()