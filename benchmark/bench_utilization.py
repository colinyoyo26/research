import subprocess
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

model_names = ['NASNetMobile']
batch_sizes = [1]
compilers = ['tvm']
tvm_assign_methods = ['default', 'method5', 'wavefront',]
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size):
    python = sys.executable

    nvprof_command = ['nsys', 'nvprof', '--print-gpu-trace', '--profile-from-start', 'off']
    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--tvm_assign_method', tvm_assign_method, 
        '--compiler', compiler,'--model_name', model_name, '--batch_size', str(batch_size)]

    print(f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}:')

    command = run_model_command + ['--print_time', 'true']
    subprocess.run(command)

    log_file = f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}.log'
    command = nvprof_command + run_model_command
    ps = subprocess.run(command, capture_output=True)
    open(log_file, 'wb').write(ps.stdout)

    #print(f'active ratio: {active_ratio}')
    #print(f'kernel time: {kernel_time / 1e6}')
    
if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run('mkdir -p logs', shell=True)

    for compiler in compilers:
        for model_name in model_names:
            if compiler == 'tvm':
                for tvm_assign_method in tvm_assign_methods:
                    for batch_size in batch_sizes:
                        doit(compiler, model_name, tvm_assign_method, batch_size)
            else:
                for batch_size in batch_sizes:
                    doit(compiler, model_name, 'default', batch_size)
                    
