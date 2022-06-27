import subprocess
import sys
import os
import json
import pandas as pd

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

#model_names = ['NASNetMobile', 'ResNeXt50', 'Ensemble[NASNetMobile_ResNeXt50]', 'Ensemble[NASNetMobile_ResNet50]']
model_names = ['NASNetMobile', 'ResNeXt50', 'Ensemble[NASNetMobile_NASNetMobile]', 'Ensemble[NASNetMobile_ResNeXt50]', 
               'Ensemble[NASNetMobile_ResNet50]', 'Ensemble[ResNeXt50_ResNeXt50]', 'Ensemble[ResNeXt50_ResNet50]',
               'Ensemble[ResNet50_ResNet50]', 'Ensemble[NASNetMobile_ResNeXt50_ResNet50]']
model_names = model_names[7:8]
#model_names = ['NASNetMobile', 'Ensemble[ResNeXt50_ResNeXt50]', 'Ensemble[NASNetMobile_NASNetMobile]', 'Ensemble[NASNetMobile_ResNeXt50_ResNet50]']

batch_sizes = [8]
compilers = ['tvm']
tvm_assign_methods = ['bfs', 'method2']
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size, res_file):
    python = sys.executable

    log_file = f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}'
    log_launch_file = f'logs/{compiler}_{model_name}_default_{batch_size}_launch.log'

    profile_command = ['nsys', 'profile', '-c', 'cudaProfilerApi', '--export', 'sqlite', '-f', 'true', '-o', 'report']
    stats_command = ['nsys', 'stats', 'report.sqlite', '-f', 'csv,table', '--report', 'gpukernsum,cudaapisum', 
                            '--force-overwrite', 'true', '-o', log_file]
    
    ncu_command = ['ncu', '--replay-mode', 'range', '--set', 'full', '-f', '-o', 'ncu_tmp']
    ncu_stats_command = ['ncu', '--import', 'ncu_tmp.ncu-rep', '-f', '--csv', '--log-file', log_file + '.log']

    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--tvm_assign_method', tvm_assign_method, 
        '--compiler', compiler, '--model_name', model_name, '--batch_size', str(batch_size)]

    label = f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}'
    print(label, ':')

    command = run_model_command + ['--print_time', 'true', '--res_file', res_file]
    subprocess.run(command)

    if tvm_assign_method == 'default':
        command = ['ncu', '--profile-from-start', 'off', '--set', 'default', '-f', '-o', 'ncu_tmp'] + run_model_command
        subprocess.run(command, capture_output=True)
        subprocess.run(['ncu', '--import', 'ncu_tmp.ncu-rep', '-f', '--csv', '--log-file', log_launch_file]) 
    
    command = profile_command + run_model_command
    subprocess.run(command, capture_output=True)
    subprocess.run(stats_command, capture_output=True)

    command = ncu_command + run_model_command
    subprocess.run(command, capture_output=True)
    subprocess.run(ncu_stats_command)
    
    write_metrics(log_file + '.log', log_launch_file, res_file, label)

def write_metrics(log_file, log_launch_file, res_file, res_entry):
    res_json = json.load(open(res_file, 'r'))
    log_launch_table = pd.read_table(log_launch_file, skiprows=[0], sep=',', 
        usecols=[4, 9, 11], names=['kernel_name', 'metric_name', 'value']) # per kernel log
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

    for i in range(len(log_table)):
        metric_name = log_table.metric_name[i]
        unit = log_table.unit[i]
        value = log_table.value[i]
        if metric_name in keys.keys():
            key = keys[metric_name]
            if key == 'duration':
                value = {'second': 1e3, 
                         'msecond': 1, 
                         'usecond': 1e-3, 
                         'nsecond': 1e-6}[unit] * float(value)
            res_json[res_entry][key] = value
            

    
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
                    
