''' nnflex.py: The main hook into the nnflex framework.

Notes:



'''
import argparse
import yaml

import onnxruntime as rt

from accelerators import Nio
from translator.onnx2flex import ONNX2Flex
import numpy as np


def configure_accelerator(yaml_config):
    print("Configuring Accelerator from: ", yaml_config)
    with open(yaml_config, 'r') as file:
        parsed_config = yaml.load(file, Loader=yaml.SafeLoader)
    
    if "accelerator" not in parsed_config:
        raise ValueError("NNFlex requires the user to request for an accelerator. Example: 'accelerator: nio'")

    accelerator = parsed_config["accelerator"]
    if accelerator == "nio":
        if "num_tile_rows" not in parsed_config:
            raise ValueError("Nio requires the num_tile_rows to be defined.")

        if "num_tile_cols" not in parsed_config:
            raise ValueError("Nio requires the num_tile_cols to be defined.")

        num_tile_rows = parsed_config["num_tile_rows"]
        num_tile_cols = parsed_config["num_tile_cols"]

        return Nio(num_tile_rows = num_tile_rows, num_tile_cols = num_tile_cols)
    else:
        raise Exception("Accelerator not supported.")


def train(model, onnx2flex, accelerator):
    '''

    '''
    raise NotImplementedError("Training is not yet implemented.")


def inference(model, onnx2flex, accelerator):
    '''
    '''
    # First, fetch the input:
    name, shape, dtype = onnx2flex.get_input_attributes()
    # Using the size of the input,
    # create a random tensor.
    new_tensor = np.random.random_sample(shape).astype(dtype)

    # new_tensor = tensor

    # Now, set the input as the random tensor
    onnx2flex.set_input(name, new_tensor)

    print("Executing Inference:\n")

    layer = onnx2flex.next_layer()
    while layer is not None:
        prev_layer = layer
        accelerator.forward(layer)
        layer = onnx2flex.next_layer()

    sess = rt.InferenceSession(model)
    input_name = sess.get_inputs()[0].name
    pred_onx = sess.run(None, {input_name: new_tensor})[0]

    if np.allclose(onnx2flex.get_output(), pred_onx):
        print("NNFlex Matches ONNX Runtime.")
    else:
        print("NNFlex Mismatch: Results are not equal with respect to ONNX Runtime")
        print("ONNX Runtime: " + str(pred_onx))
        print("NNFlex: " + str(onnx2flex.get_output()))


def main():
    parser = argparse.ArgumentParser(description="NNFlex: A Flexible Neural Network Accelerator Simulation Engine")
    parser.add_argument('-m','--model', help='The ONNX File representing the Neural Network', required=True)
    parser.add_argument('-c','--config', help="The YAML file representing the configuation of the accelerator", required=True)
    parser.add_argument('--train', action='store_true',  default=False, help='Trains the network with the request accelerator (Default: False)')    

    args = parser.parse_args()

    onnx2flex = ONNX2Flex(args.model)
    onnx2flex.translate()
    accelerator = configure_accelerator(args.config)

    if args.train:
        train(args.model, onnx2flex, accelerator)
    else:
        inference(args.model, onnx2flex, accelerator)



if __name__ == "__main__":
    main()
