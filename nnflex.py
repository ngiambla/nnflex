import onnx
import argparse

from accelerators.ngaccel import ngaccel




def main():
	parser = argparse.ArgumentParser(description="Flexible Neural Network Accelerator Simulation Engine")
	parser.add_argument('-m','--model', help='Neural Network in ONNX', required=True)
	parser.add_argument('-c','--config', help='Accelerator Configuration', required=True)	
	parser.parse_args()