import tensorflow as tf
import numpy as np
import argparse
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
import utils
from utils import cuda

def get_compiled(model, compiler):
    if compiler == 'tf':
        compiled = tf.function(lambda x : model.call(x, training=False),
                          input_signature=[tf.TensorSpec((batch_size, 224, 224, 3), tf.float32)],
                          jit_compile=False)

    elif compiler == 'tvm':
        graph_executor = utils.tvm.compile.tfv2_to_graph_executor(model)
        compiled = lambda x : graph_executor.run()

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

    model = utils.tf.model.select_model(model_name)
    predictor = get_compiled(model, compiler)
    xs = np.random.rand(max(n, warm_size), 224, 224, 3)

    if warmup:
        for i in range(0, warm_size, batch_size):
            predictor(xs[i: i + batch_size])

    cuda.rt.prof_start()
    for i in range(0, n, batch_size):
        predictor(xs[i: i + batch_size])
    cuda.rt.prof_stop()
