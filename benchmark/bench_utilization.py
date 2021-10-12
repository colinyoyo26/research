import subprocess
import sys
import os

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

model_names = ['NASNetMobile', 'MobileNet', 'ResNet50']
batch_sizes = [1, 4, 8]
nr_inputs = 1

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable

    nvprof_command = ['nvprof', '--csv', '--print-gpu-trace',
        '--profile-from-start', 'off', '--log-file', '']
    nvprof_metrics = ['--metrics', 'sm_efficiency']
    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--model_name', '', '--batch_size', '']

    log_files = []

    for model_name in model_names:
        for batch_size in batch_sizes:
            run_model_command[7] = model_name
            run_model_command[9] = str(batch_size)

            sm_log_file =  f'{model_name}_{batch_size}_sm.log'
            nvprof_command[6] = sm_log_file
    
            command = nvprof_command + nvprof_metrics + run_model_command
            subprocess.run(command)

            log_file = f'{model_name}_{batch_size}.log'
            nvprof_command[6] = log_file
            command = nvprof_command + run_model_command
            subprocess.run(command)

            log_files.append((sm_log_file, log_file))
    
    overall_sm_efficiency = []
    for sm_log_file, log_file in log_files:
        sm_extracted = nvlog.extract.extract_kernel_tf(sm_log_file)
        extracted = nvlog.extract.extract_kernel_tf(log_file)
        sm_efficiency = nvlog.process.process_log(extracted, sm_extracted)
        overall_sm_efficiency.append(sm_efficiency)
        
        model_name = log_file.rstrip('.log')
        print(f'{model_name}: {sm_efficiency}')
