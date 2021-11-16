def _assert_same_kernels(logs1: list, logs2: list):
    assert(len(logs1) == len(logs2) or \
        print(f'file length are not the same {len(logs1)} != {len(logs2)}'))
    
    for i in range(len(logs1)):
        kernel_name1 = logs1[i].rstrip('\n').split('\"')[-2]
        kernel_name2 = logs2[i].rstrip('\n').split('\"')[-2]
        assert(kernel_name1 == kernel_name2 or \
            print(f'kernels are not the same, line: {i}'))

def _get_kernel_lines(log_file: str):
    lines = open(log_file).readlines()

    is_valid = lambda line : 'NVIDIA' in line and not 'CUDA' in line
    return [ line for line in lines if is_valid(line) ]

def extract_kernel_tf(log_file: str, sm_log_file: str):
    log_lines = _get_kernel_lines(log_file)
    sm_log_lines = _get_kernel_lines(sm_log_file)

    _assert_same_kernels(log_lines, sm_log_lines)

    extracted_lines = []
    for dur_line, sm_line in zip(log_lines, sm_log_lines):
        kernel_name = dur_line.rstrip('\n').split('\"')[-2]
        dur = dur_line.split(',')[1]
        sm_efficiency = sm_line.split(',')[-2]
        achieved_occupancy = sm_line.split(',')[-1]
        extracted_lines.append(f'\"{kernel_name}\"${dur}${sm_efficiency}${achieved_occupancy}')

    extracted_file = log_file.rstrip('log') + 'extracted.log'
    with open(extracted_file, 'w') as fout:
        for line in extracted_lines:
            fout.write(line)
    return extracted_file
