import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2

import tvm.relay as relay
import tvm
from tvm.contrib import graph_executor

def tfv2_to_graph_executor(model):
    tf_func = tf.function(lambda x : model.call(x), 
                          input_signature=[tf.TensorSpec([1, 224, 224, 3], tf.float32)], 
                          jit_compile=False)
    frozen = convert_variables_to_constants_v2(tf_func.get_concrete_function())
    mod, params = relay.frontend.from_tensorflow(frozen.graph.as_graph_def())
    target = tvm.target.cuda()
    with tvm.transform.PassContext(opt_level=3):
        lib = relay.build(mod, target, params=params)
    dev = tvm.cuda(0)
    return graph_executor.GraphModule(lib["default"](dev))
