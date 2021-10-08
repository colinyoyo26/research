import subprocess
import sys
import os

model_names = ['nasnet_mobile']
batch_sizes = [1]
nr_inputs = 1

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable

    nvprof_command = ['nvprof', '--csv', '--print-gpu-trace',
        '--profile-from-start', 'off', '--log-file', '']
    nvprof_metrics = ['--metrics', 'sm_efficiency']
    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--warmup', 'true', '--model_name', '', '--batch_size', '']

    for model_name in model_names:
        for batch_size in batch_sizes:
            run_model_command[7] = model_name
            run_model_command[9] = str(batch_size)
            nvprof_command[6] = model_name + str(batch_size) + '_sm.log'
            command = nvprof_command + nvprof_metrics + run_model_command
            subprocess.run(command)

            nvprof_command[6] = model_name + str(batch_size) + '.log'
            command = nvprof_command + run_model_command
            subprocess.run(command)
