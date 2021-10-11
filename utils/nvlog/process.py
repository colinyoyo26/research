def _assert_same_kernels(logs1: list, logs2: list):
    assert(len(logs1) == len(logs2) or \
        print(f'file length are not the same {len(logs1)} != {len(logs2)}'))
    
    for i in range(len(logs1)):
        kernel_name1 = logs1[i].rstrip('\n').split('\"')[-2]
        kernel_name2 = logs2[i].rstrip('\n').split('\"')[-2]
        assert(kernel_name1 == kernel_name2 or \
            print(f'kernels are not the same, line: {i}'))

def process_log(extracted_file: str, extracted_sm_file):
    extracted_logs = open(extracted_file).readlines()
    extracted_sm_logs = open(extracted_sm_file).readlines()

    _assert_same_kernels(extracted_logs, extracted_sm_logs)

    kernel_dur = []
    kernel_sm_efficiency = []

    for dur_line, sm_line in zip(extracted_logs, extracted_sm_logs):
        kernel_dur.append(float(dur_line.split(',')[1]))
        kernel_sm_efficiency.append(float(sm_line.split(',')[-1]))

    total_sm_efficiency = \
        sum([ d * e for d, e in zip(kernel_dur, kernel_sm_efficiency) ])
    total_kernel_time = sum(kernel_dur)
    
    return total_sm_efficiency / total_kernel_time
