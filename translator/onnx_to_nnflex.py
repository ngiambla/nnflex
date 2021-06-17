import onnx
from onnx import numpy_helper

def onnx_to_nnflex(model_file):
    model = onnx.load(model_file)
    for initializer in model.graph.initializer:
        print(initializer.name)
        W = numpy_helper.to_array(initializer)
        print(W)
        print(W.shape)

    for node in model.graph.node:
        print(node.name)
        print(node.input)


    # # iterate through inputs of the graph
    # for input in model.graph.input:
    #     print (input.name, end=": ")
    #     # get type of input tensor
    #     tensor_type = input.type.tensor_type
    #     # check if it has a shape:
    #     if (tensor_type.HasField("shape")):
    #         # iterate through dimensions of the shape:
    #         for d in tensor_type.shape.dim:
    #             # the dimension may have a definite (integer) value or a symbolic identifier or neither:
    #             if (d.HasField("dim_value")):
    #                 print (d.dim_value, end=", ")  # known dimension
    #             elif (d.HasField("dim_param")):
    #                 print (d.dim_param, end=", ")  # unknown dimension with symbolic name
    #             else:
    #                 print ("?", end=", ")  # unknown dimension with no name
    #     else:
    #         print ("unknown rank", end="")
    # print()