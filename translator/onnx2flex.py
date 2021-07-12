''' onnx2flex.py

'''

import onnx
from onnx import numpy_helper, helper, shape_inference, TensorProto

import numpy as np


from operators import *


class ONNX2Flex:
    ''' ONNX2Flex
    This class provides an abstraction to map ONNX data-structures into our simulator
    frameworks.

    This is an important abstraction: this interfaces acts as a compiler, and compiles
    all layers of a model into rudimentary operations, intended for a specific hardware device.

    Args:
        onnx_model_path: a string representing the path to the ONNX mode.
        verbose: a boolean flag indicating if we should output additonal debug messages.
        check_model: a boolean flag to ask ONNX if the ONNX model is correct and valid.

    Returns:
        an ONNX2Flex object.
    '''
    def __init__(self, onnx_model_path, verbose = False, check_model = False):
        if check_model:
            onnx.checker.check_model(onnx_model_path)

        self._onnx_model = onnx.load(onnx_model_path)
        self._onnx_model = shape_inference.infer_shapes(self._onnx_model)
        self._ir_version = self._onnx_model.ir_version

        self._compute_graph = None
        
        self._tensors = dict()
        self._nodes = dict()
        self._node_outputs = dict()

        self._verbose = False

        self._anon_nodes = None

        self._node_iter = 0
        self._node_list = list()

    def get_input_attributes(self):
        for ins in self._onnx_model.graph.input:
            return ins.name, self._tensors[ins.name].shape, self._tensors[ins.name].dtype

    def set_input(self, name, tensor):
        np.copyto(self._tensors[name], tensor)

    def get_output(self):
        for outs in self._onnx_model.graph.output:
            return self._tensors[outs.name]        

    def next_layer(self):
        if self._node_iter >= len(self._node_list):
            return None
        index = self._node_iter
        self._node_iter += 1
        return self._node_list[index]


    def translate(self):
        ''' translate:
            Translates the model from ONNX to NNFlex's
            custom NN handler

        '''
        print("Translating ONNX Model to FlexNodes:")
        model = self._onnx_model
        for initializer in model.graph.initializer:
            self._tensors[initializer.name] = numpy_helper.to_array(initializer)

        for ins in model.graph.input:
            self._tensors[ins.name] = self._generate_io_tensor(ins)

        for outs in model.graph.output:
            self._tensors[outs.name] = self._generate_io_tensor(outs)

        for layer_outs in model.graph.value_info:
            self._tensors[layer_outs.name] = self._generate_io_tensor(layer_outs)

        for node in model.graph.node:
            self._translate_node(node)

    def _generate_io_tensor(self, tensor):
        tensor_type = tensor.type.tensor_type
        element_type = tensor_type.elem_type
        if element_type == TensorProto.DataType.UINT8:
            element_type = np.uint8
        elif element_type == TensorProto.DataType.INT8:
            element_type = np.int8
        elif element_type == TensorProto.DataType.UINT16:
            element_type = np.uint16
        elif element_type == TensorProto.DataType.INT16:
            element_type = np.int16
        elif element_type == TensorProto.DataType.UINT32:
            element_type = np.uint32
        elif element_type == TensorProto.DataType.INT32:
            element_type = np.int32
        elif element_type == TensorProto.DataType.UINT64:
            element_type = np.uint64
        elif element_type == TensorProto.DataType.INT64:
            element_type = np.int64
        elif element_type == TensorProto.DataType.FLOAT16:
            element_type = np.float16
        elif element_type == TensorProto.DataType.FLOAT:
            element_type = np.float32
        else:
            raise NotImplementedError("Unsupported DataType")

        dims = []
        if not tensor_type.HasField("shape"):
            raise NotImplementedError("Cannot infer shapes.")            
        for d in tensor_type.shape.dim:
            if d.HasField("dim_value"):
                dims.append(int(d.dim_value))
            else:
                raise NotImplementedError("Currently not handling symbolic dimensions.")

        return np.zeros(shape=tuple(dims), dtype=element_type)

    def get_inputs_to_node(self, node):
        '''
        '''
        inputs = list() 
        for ins in node.input:
            if ins not in self._tensors:
                raise RuntimeError("Could not find input ("+ins+") for node: "+str(node.name))
            inputs.append(self._tensors[ins])

        return inputs

    def get_outputs_of_node(self, node):
        '''
        '''
        outputs = list() 
        for outs in node.output:
            if outs not in self._tensors:
                raise RuntimeError("Could not find input ("+outs+") for node: "+str(node.name))
            outputs.append(self._tensors[outs])

        return outputs



    def _find_tensor(self, name):
        '''
        '''
        pass

    def _translate_node(self, node):
        '''
        '''
        if node.name in self._nodes:
            raise RuntimeError("Node: " + node.name + " was already translated.")

        print("\tTranslating: "+node.name)

        if self._verbose:
            print(node)

        inputs = self.get_inputs_to_node(node)
        outputs = self.get_outputs_of_node(node)


        flexnode = self._create_flexnode(node, inputs, outputs)
        self._nodes[node.name] = flexnode
        self._node_list.append(flexnode)



    def _create_flexnode(self, node, inputs, outputs):
        '''
        Creates a flexnode, which will be used to "compile" a layer into 
        rudimentary operations (suitable for an accelerator).

        This could be customized, and should be explored. 

        In the future, I would recommend to specialize these alongside an accelerator.

        Args:
            node: ONNX Node
            inputs: Inputs to the ONNX Node
            outputs: Outputs of the ONNX Node
        '''
        op_type = node.op_type;

        # Commented code is TODO.
        # if op_type == "Abs" : return ElementWise(node, inputs, outputs, "Abs")
        # if op_type == "Add" : return ElementWise(node, inputs, outputs, "Add")
        # if op_type == "AveragePool" : return AveragePool(node, inputs, outputs)
        # if op_type == "BatchNormalization" : return BatchNormalization(node, inputs, outputs)
        # if op_type == "Ceil" : return ElementWise(node, inputs, outputs, "Ceil")
        # if op_type == "Concat" : return Concat(node, inputs, outputs)
        # if op_type == "Constant" : return Constant(node, inputs, outputs)
        if op_type == "Conv" : return Conv(node, inputs, outputs)
        # if op_type == "ConvInteger" : return ConvInteger(node, inputs, outputs)
        # if op_type == "Div" : return Arithmetic(node, inputs, outputs, "Div")
        # if op_type == "Dropout" : return Dropout(node, inputs, outputs)
        # if op_type == "DynamicQuantizeLinear" : return DynamicQuantizeLinear(node, inputs, outputs)
        # if op_type == "Flatten" : return Flatten(node, inputs, outputs)
        # if op_type == "Floor" : return Elementwise(node, inputs, outputs, "Floor")
        # if op_type == "GlobalAveragePool" : return GlobalAveragePool(node, inputs, outputs)
        if op_type == "Gemm" : return GeMM(node, inputs, outputs)
        # if op_type == "LSTM" :return LSTM(node, inputs, outputs)
        # if op_type == "MatMul" : return MatMul(node, inputs, outputs)
        # if op_type == "MatMulInteger" : return MatMulInteger(node, inputs, outputs)
        # if op_type == "MaxPool" : return MaxPool(node, inputs, outputs)
        # if op_type == "Mul" : return Arithmetic(nodes, inputs, outputs, "Mul")
        if op_type == "Relu" : return ReLU(node, inputs, outputs)
        if op_type == "Reshape" : return Reshape(node, inputs, outputs)
        # if op_type == "Sigmoid" : return Sigmoid(node, inputs, outputs)
        # if op_type == "Squeeze" : return Squeeze(node, inputs, outputs)
        # if op_type == "Softmax" : return Softmax(node, inputs, outputs)
        if op_type == "Transpose" : return Transpose(node, inputs, outputs)
        # if op_type == "Unsqueeze" : return Unsqueeze(node, inputs, outputs)
        raise NotImplementedError("Operation is not implemented: "+str(op_type))
