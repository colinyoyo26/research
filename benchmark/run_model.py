import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
import tvm
from tvm.contrib import graph_executor
from tvm.contrib.cuda_graph import cuda_graph_executor

import numpy as np
import argparse
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
import utils
from utils import cuda

def get_compiled(model_name, compiler):
    model = utils.tf.model.select_model(model_name)
    input_shape = (batch_size, 224, 224, 3)
    tf_func = tf.function(lambda x : model.call(x, training=False),
        input_signature=[tf.TensorSpec(input_shape, tf.float32)],
        jit_compile=False)

    if compiler == 'tf':
        compiled = tf_func

    elif compiler in ['tvm', 'tvm_cuda_graph']:
        tvm_cache = f'./tvm_cache/{model_name}_{batch_size}'
        if not os.path.exists(tvm_cache + '.so'):
            json, lib, params = utils.tvm.util.build_from_tfv2(tf_func)
            os.system('mkdir -p tvm_cache')
            utils.tvm.util.save(json, lib, params, tvm_cache)
        json, lib, param = utils.tvm.util.load(tvm_cache)
        dev = tvm.cuda(0)
        
        if compiler == 'tvm':
            executor = graph_executor.create(json, lib, dev)
        elif compiler == 'tvm_cuda_graph':
            executor = cuda_graph_executor.create(json, lib, dev)
        
        compiled = lambda x : executor.run()

    else:
        exit(1)

    return compiled

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=60000, help='number of images')
    parser.add_argument('--batch_size', type=int, default=1, help='batch size')
    parser.add_argument('--model_name', type=str, default='NASNetMobile', help='model name')
    parser.add_argument('--compiler', type=str, default='tf', help='compiler to compile the model')
    parser.add_argument('--warmup', type=bool, default=False, help='use 100 inputs to warm up for jit')
    args = vars(parser.parse_args())

    n = args['n']
    batch_size = args['batch_size']
    model_name = args['model_name']
    compiler = args['compiler']
    warmup = args['warmup']

    n = (n + batch_size - 1) // batch_size * batch_size
    warm_size = (100 + batch_size - 1) // batch_size * batch_size

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
        exit(1)

    predictor = get_compiled(model_name, compiler)
    xs = np.random.rand(max(n, warm_size), 224, 224, 3)

    if warmup:
        for i in range(0, warm_size, batch_size):
            predictor(xs[i: i + batch_size])

    cuda.rt.prof_start()
    for i in range(0, n, batch_size):
        predictor(xs[i: i + batch_size])
    cuda.rt.prof_stop()
