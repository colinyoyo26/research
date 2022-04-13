import subprocess
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

model_names = ['ResNeXt50', 'Ensemble[NASNetMobile_ResNeXt50]', 'Ensemble[NASNetMobile_ResNet50]']
#model_names = ['NASNetMobile']
batch_sizes = [8]
compilers = ['tvm']
tvm_assign_methods = ['default', 'wavefront', 'method5']
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size):
    python = sys.executable

    log_file = f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}'

    profile_command = ['nsys', 'profile', '-c', 'cudaProfilerApi', '--export', 'sqlite', '-f', 'true', '-o', 'report']
    stats_command = ['nsys', 'stats', 'report.sqlite', '-f', 'csv,table', '--report', 'gpukernsum,cudaapisum', 
                            '--force-overwrite', 'true', '-o', log_file]
    
    ncu_command = ['ncu', '--replay-mode', 'range', '--set', 'full', '-f', '-o', 'ncu_tmp']
    ncu_stats_command = ['ncu', '--import', 'ncu_tmp.ncu-rep', '-f', '--log-file', log_file + '.log']

    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--tvm_assign_method', tvm_assign_method, 
        '--compiler', compiler,'--model_name', model_name, '--batch_size', str(batch_size)]

    print(f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}:')

    command = run_model_command + ['--print_time', 'true']
    subprocess.run(command)

    command = profile_command + run_model_command
    subprocess.run(command, capture_output=True)
    subprocess.run(stats_command, capture_output=True)

    command = ncu_command + run_model_command
    subprocess.run(command, capture_output=True)
    subprocess.run(ncu_stats_command)    
    
if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run('mkdir -p logs', shell=True)

    for compiler in compilers:
        for model_name in model_names:
            for batch_size in batch_sizes:
                if compiler == 'tvm':
                    for tvm_assign_method in tvm_assign_methods:
                        doit(compiler, model_name, tvm_assign_method, batch_size)
                else:
                    for batch_size in batch_sizes:
                        doit(compiler, model_name, 'default', batch_size)
                    
