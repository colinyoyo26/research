def _assert_same_kernels(logs1: list, logs2: list):
    assert(len(logs1) == len(logs2) or \
        print(f'file length are not the same {len(logs1)} != {len(logs2)}'))
    
    for i in range(len(logs1)):
        kernel_name1 = logs1[i][0]
        kernel_name2 = logs2[i][0]
        assert(kernel_name1 == kernel_name2 or \
            print(f'kernels are not the same, kernel: {kernel_name1}, {kernel_name2}'))

def _get_kernel_lines(log_file: str):
    lines = open(log_file).readlines()

    is_valid = lambda line : 'NVIDIA' in line and not 'CUDA' in line
    return [ line for line in lines if is_valid(line) ]

def _get_time_scale(log_file: str):
    lines = open(log_file).readlines()
    i = 0
    while lines[i][0] in ['=', '\"']:
        i += 1
    units = lines[i].split(',')
    scale_dict = {'s': 1e6, 'ms': 1e3, 'us': 1.}
    return (scale_dict[units[0]], scale_dict[units[1]])

def _extract_log_lines(lines: str, time_scales):
    extracted = []
    for line in lines:
        kernel_name = line.rstrip('\n').split('\"')[-2]
        stream_id = line.split(',')[-3]
        start_time = float(line.split(',')[0]) * time_scales[0]
        dur = float(line.split(',')[1]) * time_scales[1]
        extracted.append((kernel_name, stream_id, start_time, dur))
    return extracted

def _extract_metric_lines(lines: str):
    extracted = []
    for line in lines:
        kernel_name = line.rstrip('\n').split('\"')[-2]
        sm_efficiency = line.split(',')[-2]
        achieved_occupancy = line.split(',')[-1]
        extracted.append((kernel_name, sm_efficiency, achieved_occupancy))
    return extracted

def extract_kernel_tf(log_file: str, sm_log_file: str):
    log_lines = _get_kernel_lines(log_file)
    time_scales = _get_time_scale(log_file)
    sm_log_lines = _get_kernel_lines(sm_log_file)

    log_lines = _extract_log_lines(log_lines, time_scales)
    sm_log_lines = _extract_metric_lines(sm_log_lines)

    log_lines = sorted(log_lines, key=lambda x : x[0])
    sm_log_lines = sorted(sm_log_lines, key=lambda x : x[0])

    _assert_same_kernels(log_lines, sm_log_lines)

    extracted_lines = []
    for log_line, sm_line in zip(log_lines, sm_log_lines):
        kernel_name = log_line[0]
        stream_id = log_line[1]
        start_time = log_line[2]
        dur = log_line[3]
        sm_efficiency = sm_line[1]
        achieved_occupancy = sm_line[2]
        extracted_lines.append(f'\"{kernel_name}\"${stream_id}${start_time}${dur}${sm_efficiency}${achieved_occupancy}')

    extracted_file = log_file.rstrip('log') + 'extracted.log'
    with open(extracted_file, 'w') as fout:
        for line in extracted_lines:
            fout.write(line)
    return extracted_file
