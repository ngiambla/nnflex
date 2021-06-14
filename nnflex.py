import onnx
import argparse

from accelerators.nacl.nacl import NaCl, NaClSupportLayer


class Tensor():
	def __init__(self, data_list):
		self.data = data_list



def main():
	# parser = argparse.ArgumentParser(description="Flexible Neural Network Accelerator Simulation Engine")
	# parser.add_argument('-m','--model', help='Neural Network in ONNX', required=True)
	# parser.add_argument('-c','--config', help='Accelerator Configuration', required=True)	
	# parser.parse_args()

	local_nacl = NaCl(num_tile_rows=1, num_tile_cols=1)

	in_acts = Tensor(list(range(1, 5)))
	weights = Tensor(list(range(1, 5)))
	outputs = Tensor(list(range(1, 5)))
	local_nacl.forward("elemwiseadd", in_acts, weights, outputs)
	print(outputs.data)



if __name__ == "__main__":
	main()