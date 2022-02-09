import subprocess
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

model_names = ['NASNetMobile', 'ResNet50']
batch_sizes = [1, 32]
compilers = ['tvm', 'tf']
nr_inputs = 1

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable

    nvprof_command = ['nvprof', '--csv', '--print-gpu-trace', '--continuous-sampling-interval', '1',
        '--profile-from-start', 'off', '--log-file', '']
    nvprof_metrics = ['--metrics', 'sm_efficiency,achieved_occupancy']
    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--compiler', '','--model_name', '', '--batch_size', '']

    subprocess.run('mkdir -p logs', shell=True)
    log_files = []

    for compiler in compilers:
        for model_name in model_names:
            for batch_size in batch_sizes:
               run_model_command[-5] = compiler
               run_model_command[-3] = model_name
               run_model_command[-1] = str(batch_size)
               
               command = run_model_command + ['--print_time', 'true']
               subprocess.run(command)

               sm_log_file =  f'logs/{compiler}_{model_name}_{batch_size}_sm.log'
               nvprof_command[-1] = sm_log_file

               command = nvprof_command + nvprof_metrics + run_model_command
               subprocess.run(command)

               log_file = f'logs/{compiler}_{model_name}_{batch_size}.log'
               nvprof_command[-1] = log_file
               command = nvprof_command + run_model_command
               subprocess.run(command)

               log_files.append((sm_log_file, log_file))

               extracted_file = nvlog.extract.extract_kernel_tf(log_file, sm_log_file)
               active_ratio, time = nvlog.process.process_log(extracted_file)
               name = log_file.rstrip('.log').lstrip('logs/')
               print(f'{name}: {active_ratio} {time}')
