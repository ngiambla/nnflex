''' onnx2flex.py

'''

import onnx
from onnx import numpy_helper, helper, shape_inference, TensorProto

import numpy as np



class ONNX2Flex:
    '''
    '''
    def __init__(self, onnx_model_path, verbose = False, check_model = False):
        if check_model:
            onnx.checker.check_model(onnx_model_path)

        self._onnx_model = onnx.load(onnx_model_path)
        self._onnx_model = shape_inference.infer_shapes(self._onnx_model)
        self._ir_version = self._onnx_model.ir_version

        self._compute_graph = None
        self._user_inputs = list()
        
        self._tensors = dict()
        self._nodes = dict()
        self._inputs_for_node = dict()
        self._node_outputs = dict()

        self._verbose = False

        self._anon_nodes = None

    def translate(self):
        ''' translate:
            Translates the model from ONNX to NNFlex's
            custom NN handler

        '''
        model = self._onnx_model
        for initializer in model.graph.initializer:
            self._tensors[initializer.name] = numpy_helper.to_array(initializer)

        for ins in model.graph.input:
            self._tensors[ins.name] = self._generate_io_tensor(ins)

        for outs in model.graph.output:
            self._tensors[outs.name] = self._generate_io_tensor(outs)

        for layer_outs in model.graph.value_info:
            self._tensors[layer_outs.name] = self._generate_io_tensor(layer_outs)

        print(self._tensors.keys())

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
            inputs.append(ins)

        return inputs

    def get_outputs_of_node(self, node):
        '''
        '''
        outputs = list() 
        for outs in node.output:
            if outs not in self._tensors:
                raise RuntimeError("Could not find input ("+outs+") for node: "+str(node.name))
            outputs.append(outs)

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

        print("Translating: "+node.name)


        inputs = self.get_inputs_to_node(node)
        outputs = self.get_outputs_of_node(node)


        #flexnode = self._create_flexnode(node, inputs)

    # // onnx allows (or at least some tools create) nodes without names
    # // create unique names for those, e.g. "anonymous_5_relu"
    # if( n->onnx_name == "" ) {
    #     std::string name = "anonymous_";
    #     name += n->op_name;
    #     name +=  "_" + std::to_string(anonymous_nodes);
    #     n->onnx_name = name;
    #     anonymous_nodes++;
    # }


        # TODO DONT FORGET
        # map the new FlexNode here.
        self._nodes[node.name] = None


    # // onnx allows (or at least some tools create) nodes without names
    # // create unique names for those, e.g. "anonymous_5_relu"
    # if( n->onnx_name == "" ) {
    #     std::string name = "anonymous_";
    #     name += n->op_name;
    #     name +=  "_" + std::to_string(anonymous_nodes);
    #     n->onnx_name = name;
    #     anonymous_nodes++;
    # }

    # if( node.attribute_size() != 0 )
    #     n->parseAttributes( node );



    def _create_flexnode(self, node, inputs):
        '''
        '''
        op_type = node.op_type();

        # if op_type == "Abs" : return ElementWise(node, inputs, "Abs")
        # if op_type == "Add" : return ElementWise(node, inputs, "Add")
        # if op_type == "AveragePool" : return AveragePool(node, inputs)
        # if op_type == "BatchNormalization" : return BatchNormalization(node, inputs)
        # if op_type == "Ceil" : return ElementWise(node, input, "Ceil")
        # if op_type == "Concat" : return Concat(node, inputs)
        # if op_type == "Constant" : return Constant(node, inputs)
        # if op_type == "Conv" : return Conv(node, inputs)
        # if op_type == "ConvInteger" : return ConvInteger(node, inputs)
        # if op_type == "Div" : return Arithmetic(node, inputs, "Div")
        # if op_type == "Dropout" : return Dropout(node, inputs)
        # if op_type == "DynamicQuantizeLinear" : return DynamicQuantizeLinear(node, inputs)
        # if op_type == "Flatten" : return Flatten(node, inputs)
        # if op_type == "Floor" : return Elementwise(node, inputs, "Floor")
        # if op_type == "GlobalAveragePool" : return GlobalAveragePool(node, inputs)
        # if op_type == "Gemm" : return GEMM(node, inputs)
        # if op_type == "LSTM" :return LSTM(node, inputs)
        # if op_type == "MatMul" : return MatMul(node, inputs)
        # if op_type == "MatMulInteger" : return MatMulInteger(node, inputs)
        # if op_type == "MaxPool" : return MaxPool(node, inputs)
        # if op_type == "Mul" : return Arithmetic(nodes, inputs, "Mul")
        # if op_type == "Relu" : return ReLu(node, inputs)
        # if op_type == "Reshape" : return Reshape(node, inputs)
        # if op_type == "Sigmoid" : return Sigmoid(node, inputs)
        # if op_type == "Squeeze" : return Squeeze(node, inputs)
        # if op_type == "Softmax" : return Softmax(node, inputs)
        # if op_type == "Transpose" : return Transpose(node, inputs)
        # if op_type == "Unsqueeze" : return Unsqueeze(node, inputs)

        raise NotImplementedError("Operation is not implemented: "+str(op_type))
