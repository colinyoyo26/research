from collections import defaultdict
import pandas as pd

def get_kernel_info(log_file: str):
    table = pd.read_table(log_file, skiprows=[0], sep=',', 
        usecols=[3, 8], names=['duration', 'kernel_name'])
    kernel_info = defaultdict(lambda : {'duration' : 0})
    for i in range(len(table)):
        kernel_name, duration = table.kernel_name[i], table.duration[i]
        kernel_name = kernel_name[: len(kernel_name) - 8]
        kernel_info[kernel_name]['duration'] += float(str(duration).replace(',', ''))
    return kernel_info
