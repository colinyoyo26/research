from collections import defaultdict
import pandas as pd

def get_kernel_info(log_file: str):
    launch_stat_file =  log_file.rstrip('gpukernsum.csv') + 'launch.log'
    table = pd.read_table(launch_stat_file, skiprows=[0, 1, 2, 3, 4], sep=',',
        usecols=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 18], names=['duration', 'gridx', 'gridy', 'gridz',
                                                     'blkx', 'blky', 'blkz', 'reg_per_thread',
                                                     's_shr', 'd_shr', 'kernel_name'])

    kernel_info = defaultdict(lambda : {'duration': 0, 'grid_size': 0, 'block_size': 0,
                                        'threads': 0, 'registers_per_thread': 0,
                                        'warps_per_sm': 0, 'memory': 0,
                                        'dyn_mem': 0, 'stc_mem': 0})
    for i in range(len(table)):
        kernel_name = table.kernel_name[i]
        if 'CUDA' in kernel_name or kernel_name in kernel_info.keys():
            continue
        k = kernel_name[: len(kernel_name) - 8]
        kernel_info[k]['duration'] += float(table.duration[i])
        kernel_info[k]['grid_size'] = max(kernel_info[k]['grid_size'], float(table.gridx[i]) * float(table.gridy[i]) * float(table.gridz[i]))
        kernel_info[k]['block_size'] = max(kernel_info[k]['block_size'], float(table.blkx[i]) * float(table.blky[i]) * float(table.blkz[i]))
        kernel_info[k]['registers_per_thread'] = max(kernel_info[k]['registers_per_thread'], float(table.reg_per_thread[i]))
        kernel_info[k]['dyn_mem'] = max(kernel_info[k]['dyn_mem'], float(table.s_shr[i]))
        kernel_info[k]['stc_mem'] = max(kernel_info[k]['stc_mem'], float(table.d_shr[i]))

    return kernel_info
