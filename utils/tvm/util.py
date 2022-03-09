import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2

import tvm
import tvm.relay as relay

def build_from_tfv2(tf_func):
    frozen = convert_variables_to_constants_v2(tf_func.get_concrete_function())
    mod, params = relay.frontend.from_tensorflow(frozen.graph.as_graph_def())
    target = tvm.target.cuda()
    with tvm.transform.PassContext(opt_level=3):
        json, lib, params = relay.build(mod, target, params=params)
    return json, lib, params

def save(json, lib, params, path):
    lib.export_library(path + '.so')
    open(path + '.json', 'w').write(json)
    param_bytes = tvm.runtime.save_param_dict(params)
    open(path + '.params', 'wb').write(param_bytes)

def load(path):
    lib = tvm.runtime.load_module(path + '.so')
    json = open(path + '.json').read()
    params = open(path + '.params', 'rb').read()
    #params =  tvm.runtime.load_param_dict(param_bytes)
    return json, lib, params
