from collections import defaultdict
import pandas as pd

def get_kernel_info(log_file: str):
    launch_stat_file =  log_file.rstrip('gpukernsum.csv') + 'launch.log'
    launch_stat_table = pd.read_table(launch_stat_file, skiprows=[0], sep=',', 
        usecols=[4, 9, 11], names=['kernel_name', 'metric_name', 'value'])

    table = pd.read_table(log_file, skiprows=[0], sep=',', 
        usecols=[3, 8], names=['duration', 'kernel_name'])
    kernel_info = defaultdict(lambda : {'duration': 0, 'grid_size': 0, 'block_size': 0,
                                        'threads': 0, 'registers_per_thread': 0, 
                                        'warps_per_sm': 0, 'memory': 0, 
                                        'dyn_mem': 0, 'stc_mem': 0})
    for i in range(len(table)):
        kernel_name, duration = table.kernel_name[i], table.duration[i]
        kernel_name = kernel_name[: len(kernel_name) - 8]
        kernel_info[kernel_name]['duration'] += float(str(duration).replace(',', ''))

    for i in range(len(launch_stat_table)):
        kernel_name = launch_stat_table.kernel_name[i]
        metric_name = launch_stat_table.metric_name[i] 
        value = launch_stat_table.value[i]
        kernel_name = kernel_name[: len(kernel_name) - 8]        
        assert kernel_name in kernel_info.keys()
        
        keys = {'Grid Size': 'grid_size', 'Block Size': 'block_size', 
                'Registers Per Thread': 'registers_per_thread',
                'Achieved Active Warps per SM': 'warps_per_sm',
                'Memory [%]': 'memory', 'Dynamic Shared Memory Per Block': 'dyn_mem',
                'Static Shared Memory Per Block': 'stc_mem'}

        if metric_name in keys.keys():
            key = keys[metric_name]
            kernel_info[kernel_name][key] = max(kernel_info[kernel_name][key], float(value))
    return kernel_info
