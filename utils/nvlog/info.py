from collections import defaultdict

def get_kernel_info(extracted_file: str):
    lines = open(extracted_file).readlines()
    kernel_info = defaultdict(lambda : [[], []])
    visited = set()

    for line in lines:
        kernel_name, stream_id, start_time, duration, sm_efficiency, achieved_occupacy = line.split('$')
        kernel_name = kernel_name[1: -1]
        if kernel_name in visited:
            continue
        visited.add(kernel_name)
        
        duration = float(duration)
        utilization = float(sm_efficiency) * float(achieved_occupacy)

        kernel_name = kernel_name[: len(kernel_name) - 8]
        kernel_info[kernel_name][0].append(duration)
        kernel_info[kernel_name][1].append(utilization)

    for kernel_name in kernel_info:
        utilizations, durations = kernel_info[kernel_name]
        duration = sum(durations)
        utilization = sum([u * d for u, d in zip(utilizations, durations)]) / duration
        kernel_info[kernel_name] = (utilization, duration)

    return kernel_info
