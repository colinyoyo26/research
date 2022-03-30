import numpy as np
import argparse
import time
import sys
import os
import json

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
import tvm
from tvm.contrib import graph_executor
from tvm.contrib.cuda_graph import cuda_graph_executor

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
import utils
from utils import cuda

def run_tvm(executor, x):
    executor.set_input('x', x)
    executor.run()
    return executor.get_output(0)

def run_tf(executor, x):
    return executor(x)

def get_executor(model, input_shape, compiler, tvm_assign_method, batch_size):
    input_shape = (batch_size, input_shape[0], input_shape[1], input_shape[2])
    tf_func = tf.function(lambda x : model.call(x, training=False),
        input_signature=[tf.TensorSpec(input_shape, tf.float32)],
        jit_compile=False)

    executor = None
    if compiler == 'tf':
        executor = tf_func

    elif compiler in ['tvm', 'tvm_cuda_graph']:
        tvm_cache = f'./tvm_cache/{model_name}_{batch_size}'
        if not os.path.exists(tvm_cache + '.so'):
            json, lib, params = utils.tvm.util.build_from_tfv2(tf_func)
            os.system('mkdir -p tvm_cache')
            utils.tvm.util.save(json, lib, params, tvm_cache)

        extracted_path = f'./logs/{compiler}_{model_name}_default_{batch_size}.log'
        # generate assign.json file 
        os.system(f'python ../stream_assignment/stream_assignment.py --json_path {tvm_cache}.json '
                                                                    f'--log_file {extracted_path} ' 
                                                                    f'--method {tvm_assign_method} '
                                                                    f'--model_name {model_name}')
        json, lib, params = utils.tvm.util.load(tvm_cache)
        dev = tvm.cuda(0)
        
        if compiler == 'tvm':
            executor = graph_executor.create(json, lib, dev)
            executor.load_params(params)
            executor.set_schedule('../stream_assignment/emit_order.json', '../stream_assignment/assignment.json')
        elif compiler == 'tvm_cuda_graph':
            executor = cuda_graph_executor.create(json, lib, dev)
    assert executor or print(model_name)
    return executor

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=60000, help='number of images')
    parser.add_argument('--batch_size', type=int, default=1, help='batch size')
    parser.add_argument('--model_name', type=str, default='NASNetMobile', help='model name')
    parser.add_argument('--compiler', type=str, default='tf', help='compiler to compile the model')
    parser.add_argument('--warmup', type=bool, default=False, help='use 100 inputs to warm up for jit')
    parser.add_argument('--print_time', type=bool, default=False)
    parser.add_argument('--tvm_assign_method', type=str, default='default')
    parser.add_argument('--save_res', type=bool, default=False)
    parser.add_argument('--save_dir', type=str, default='')
    args = vars(parser.parse_args())

    n = args['n']
    batch_size = args['batch_size']
    model_name = args['model_name']
    compiler = args['compiler']
    warmup = args['warmup']
    print_time = args['print_time']
    tvm_assign_method = args['tvm_assign_method']
    save_res = args['save_res']
    save_dir = args['save_dir']

    n = (n + batch_size - 1) // batch_size * batch_size
    warm_size = (100 + batch_size - 1) // batch_size * batch_size

    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
        exit(1)

    model, input_shape = utils.tf.model.select_model(model_name)
    executor = get_executor(model, input_shape, compiler, tvm_assign_method, batch_size)
    run = run_tf if compiler == 'if' else run_tvm

    xs = np.random.rand(max(n, warm_size), input_shape[0], input_shape[1], input_shape[2])
    xs = np.ones_like(xs)

    if warmup:
        for i in range(0, warm_size, batch_size):
            run(executor, xs[i: i + batch_size])

    start_time = time.time()
    
    res = []
    cuda.rt.prof_start()
    for i in range(0, n, batch_size):
        res.append(run(executor, xs[i: i + batch_size]))
    cuda.rt.prof_stop()

    elapsed = time.time() - start_time
    if print_time:
        if compiler == 'tvm':
            repeat = 100
            bench_res = executor.benchmark(tvm.cuda(0), repeat=repeat, end_to_end=True)
            res_time = (bench_res.mean * repeat - bench_res.max - bench_res.min) / (repeat - 2)
            print(res_time)
        else: 
            print('elapsed: ', elapsed)
    if save_res:
        res = [r.numpy().tolist() for r in res]
        open(save_dir, 'w').write(json.dumps(res))


