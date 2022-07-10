import subprocess
import sys
import os
import json
import pandas as pd
from collections import defaultdict

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog
from utils.sched import Graph

#model_names = ['NASNetMobile', 'ResNeXt50', 'Ensemble[NASNetMobile_ResNeXt50]', 'Ensemble[NASNetMobile_ResNet50]']
model_names = ['NASNetMobile', 'ResNeXt50', 'Ensemble[NASNetMobile_NASNetMobile]', 'Ensemble[NASNetMobile_ResNeXt50]', 
               'Ensemble[NASNetMobile_ResNet50]', 'Ensemble[ResNeXt50_ResNeXt50]', 'Ensemble[ResNeXt50_ResNet50]',
               'Ensemble[ResNet50_ResNet50]', 'Ensemble[NASNetMobile_ResNeXt50_ResNet50]']
model_names = model_names
#model_names = ['NASNetMobile', 'Ensemble[ResNeXt50_ResNeXt50]', 'Ensemble[NASNetMobile_NASNetMobile]', 'Ensemble[NASNetMobile_ResNeXt50_ResNet50]']

batch_sizes = [1]
compilers = ['tvm']
tvm_assign_methods = ['default', 'bfs', 'method2']
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size, res_file):
    python = sys.executable

    log_file = f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}'
    log_launch_file = f'logs/{compiler}_{model_name}_default_{batch_size}_launch.log'

    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--tvm_assign_method', tvm_assign_method, 
        '--compiler', compiler, '--model_name', model_name, '--batch_size', str(batch_size)]

    label = f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}'
    print(label, ':')

    command = run_model_command + ['--print_time', 'true', '--res_file', res_file, '--sched', 'true']
    subprocess.run(command)

    if tvm_assign_method == 'default':
        command = ['nvprof', '--csv', '--print-gpu-trace', '--continuous-sampling-interval', '1',
        '--profile-from-start', 'off', '--log-file', f'{log_launch_file}'] + run_model_command
        subprocess.run(command, capture_output=False)

def write_metrics(tvm_cache, log_file, log_launch_file, res_file, res_entry):
    res_json = json.load(open(res_file, 'r'))
    log_launch_table = pd.read_table(log_launch_file, skiprows=[0], sep=',', 
        usecols=[4, 9, 10, 11], names=['kernel_name', 'metric_name', 'unit', 'value']) # per kernel log
    log_table = pd.read_table(log_file, skiprows=[0], sep=',', 
        usecols=[9, 10, 11], names=['metric_name', 'unit', 'value']) # model log

    keys = {
        'Compute (SM) [%]': 'sm_throughput(%)',
        'Achieved Occupancy': 'achieved_occupancy(%)',
        'L1/TEX Hit Rate': 'L1/TEX_hit_rate(%)',
        'L2 Hit Rate': 'L2_hit_rate(%)',
        'Issued Instructions': 'instructions',
        'L1/TEX Cache Throughput': 'L1/TEX_throughput(%)',
        'L2 Cache Throughput': 'L2_throughput(%)',
        'Duration': 'duration(ms)'
    }

    unit_trans = {'second': 1e3, 'msecond': 1, 'usecond': 1e-3, 'nsecond': 1e-6}

    if res_entry not in res_json.keys():
        res_json[res_entry] = {}

    for i in range(len(log_table)):
        metric_name = log_table.metric_name[i]
        unit = log_table.unit[i]
        value = log_table.value[i]
        if metric_name in keys.keys():
            key = keys[metric_name]
            if key == 'duration(ms)':
                value = unit_trans[unit] * float(value)
            res_json[res_entry][key] = value
            
    graph = Graph(tvm_cache)
    tc = graph.get_transitive_closure(graph.get_topo())
    seq_kernels = set()
    for id in graph.get_topo():
        for o in tc[id]:
            tc[o].add(id)
        if len(tc[id]) == graph.num_tvm_op:
            seq_kernels.add(graph[id].func_name)
    
    sk_metrics = defaultdict(lambda: defaultdict(lambda: 0))
    for i in range(len(log_launch_table)):
        kernel_name = log_launch_table.kernel_name[i]
        metric_name = log_launch_table.metric_name[i]
        unit = log_launch_table.unit[i]
        value = log_launch_table.value[i]
        A = 'Achieved Occupancy'
        D = 'Duration'
        if kernel_name[: len(kernel_name) - 8] in seq_kernels and metric_name in {A, D}:
            if metric_name == D:
                value = unit_trans[unit] * float(value)
            sk_metrics[kernel_name][metric_name] = float(value)
            sk_metrics[kernel_name]['dot'] = sk_metrics[kernel_name][A] * sk_metrics[kernel_name][D]
    
    dot_sum = 0
    dur = 0
    for kernel_name in sk_metrics:
        dot_sum += sk_metrics[kernel_name]['dot']
        dur += sk_metrics[kernel_name]['Duration']

    res_json[res_entry]['fixed_achieved_occupancy(%)'] =  \
        (res_json[res_entry]['achieved_occupancy(%)'] * 
        res_json[res_entry]['duration(ms)'] - 
        dot_sum) / (res_json[res_entry]['duration(ms)'] - dur) 

    s = json.dumps(res_json, indent=2)
    open(res_file, 'w').write(s)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    res_dir = os.path.join(ROOT_PATH, 'benchmark', 'res')
    subprocess.run('mkdir -p logs', shell=True)
    subprocess.run(f'mkdir -p {res_dir}', shell=True)
    res_file = os.path.join(res_dir, 'res.json')

    for compiler in compilers:
        for model_name in model_names:
            for batch_size in batch_sizes:
                if compiler == 'tvm':
                    for tvm_assign_method in tvm_assign_methods:
                        doit(compiler, model_name, tvm_assign_method, batch_size, res_file)
                else:
                    for batch_size in batch_sizes:
                        doit(compiler, model_name, 'default', batch_size, res_file)
                    
