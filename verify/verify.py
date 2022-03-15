import subprocess
import sys
import os
import json

model_names = ['NASNetMobile']
batch_sizes = [1]
compiler = 'tvm'
tvm_assign_methods = ['default', 'wavefront', 'wavefront_stage', 'method1', 'method1_stage', 'method2']
nr_inputs = 1

def doit(compiler, model_name, tvm_assign_method, batch_size, output_dir):
    python = sys.executable

    ans_dir = os.path.join(output_dir, f'{compiler}_{model_name}_default_{batch_size}.out')
    output_dir = os.path.join(output_dir, f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}.out')

    run_model_command = [python, 'run_model.py', '--n', str(nr_inputs),
        '--tvm_assign_method', tvm_assign_method, '--compiler', compiler,
        '--model_name', model_name, '--batch_size', str(batch_size),
        '--save_res', 'true', '--save_dir', output_dir]

    print(f'{compiler}_{model_name}_{tvm_assign_method}_{batch_size}... ', end='')
    subprocess.run(run_model_command)
    
    res = json.load(open(output_dir))
    ans = json.load(open(ans_dir))
    print(('Failed', 'Pass')[res == ans])


if __name__ == '__main__':
    file_dir = os.path.dirname(os.path.abspath(__file__))
    work_dir = os.path.join(file_dir, '..', 'benchmark')
    os.chdir(work_dir)

    for model_name in model_names:
        output_dir = os.path.join(file_dir, f'{model_name}_outputs') 
        subprocess.run(f'mkdir -p {output_dir}', shell=True)
        for tvm_assign_method in tvm_assign_methods:
            for batch_size in batch_sizes:
                doit(compiler, model_name, tvm_assign_method, batch_size, output_dir)
                    
