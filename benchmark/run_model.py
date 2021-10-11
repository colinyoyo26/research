import tensorflow as tf
import numpy as np
import ctypes
import argparse
import sys
import os

from tensorflow.python import training
from tensorflow.keras.applications import NASNetMobile, EfficientNetB0, MobileNet

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import loader

_cudart = ctypes.CDLL('libcudart.so')
def cu_prof_start():
    ret = _cudart.cudaProfilerStart()
    if ret != 0:
      raise Exception('cudaProfilerStart() returned %d' % ret)

def cu_prof_stop():
    ret = _cudart.cudaProfilerStop()
    if ret != 0:
      raise Exception('cudaProfilerStop() returned %d' % ret)

def select_model(model_name: str):
    models = {'NASNetMobile': NASNetMobile,
              'EfficientNetB0': EfficientNetB0,
              'MobileNet': MobileNet}
    model = models.get(model_name)
    if model == None:
        exit(1)
    return model()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=sys.maxsize, help='number of images')
    parser.add_argument('--batch_size', type=int, default=1, help='batch size')
    parser.add_argument('--model_name', type=str, default='NASNetMobile', help='model name')
    parser.add_argument('--warmup', type=bool, default=False, help='use 100 inputs to warm up for jit')
    args = vars(parser.parse_args())
    
    n = args['n']
    batch_size = args['batch_size']
    model_name = args['model_name']
    warmup = args['warmup']
    warm_size = 100

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
        exit(1)

    model = select_model(model_name)
    tf_func = tf.function(lambda x : model.call(x, training=False), 
                          input_signature=[tf.TensorSpec((batch_size, 224, 224, 3), tf.float32)], 
                          jit_compile=False)

    xs, _ = loader.imgnet.load_datas(max(n, warm_size))

    if warmup:
        for i in range(0, warm_size, batch_size):
            tf_func(xs[i: i + batch_size])

    cu_prof_start()
    for i in range(0, n, batch_size):
        tf_func(xs[i: i + batch_size])
    cu_prof_stop()
