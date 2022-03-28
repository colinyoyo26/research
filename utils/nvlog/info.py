from collections import defaultdict
import pandas as pd

def get_kernel_info(log_file: str):
    table = pd.read_table(log_file, skiprows=[0, 1, 2, 3, 4, 5, 6, 7], delim_whitespace=True, 
        usecols=[0, 1, 18, 19], names=['start_time', 'duration', 'stream_id', 'kernel_name'])
    kernel_info = defaultdict(lambda : {'duration' : 0})
    visited = set()
    for i in range(len(table)):
        kernel_name, duration = table.kernel_name[i], table.duration[i]
        if kernel_name in visited:
            continue
        visited.add(kernel_name)
        kernel_name = kernel_name[: len(kernel_name) - 8]
        kernel_info[kernel_name]['duration'] += float(duration)
    return kernel_info
