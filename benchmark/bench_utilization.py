import subprocess
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

model_names = ['NASNetMobile']
batch_sizes = [1]
compilers = ['tvm']
tvm_assign_methods = ['test', 'default']
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size):
    python = sys.executable

    nvprof_command = ['nvprof', '--csv', '--print-gpu-trace', '--continuous-sampling-interval', '1',
        '--profile-from-start', 'off', '--log-file', '']
    nvprof_metrics = ['--metrics', 'sm_efficiency,achieved_occupancy']
    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--tvm_assign_method', '', '--compiler', '','--model_name', '', '--batch_size', '']

    print(f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}:')

    run_model_command[-7] = tvm_assign_method
    run_model_command[-5] = compiler
    run_model_command[-3] = model_name
    run_model_command[-1] = str(batch_size)
                
    command = run_model_command + ['--print_time', 'true']
    subprocess.run(command)

    sm_log_file =  f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}_sm.log'
    nvprof_command[-1] = sm_log_file

    command = nvprof_command + nvprof_metrics + run_model_command
    subprocess.run(command)

    log_file = f'logs/{compiler}_{model_name}_{tvm_assign_method}_{batch_size}.log'
    nvprof_command[-1] = log_file
    command = nvprof_command + run_model_command
    subprocess.run(command)

    extracted_file = nvlog.extract.extract_kernel_tf(log_file, sm_log_file)
    active_ratio, kernel_time = nvlog.process.process_log(extracted_file)
    print(f'active ratio: {active_ratio}')
    print(f'kernel time: {kernel_time / 1e6}')
    
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
                    
