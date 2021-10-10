def process_log(extracted_file: str, extracted_sm_file):
    extracted_logs = open(extracted_file).readlines()
    extracted_sm_logs = open(extracted_sm_file).readlines()

    kernel_dur = []
    kernel_sm_efficiency = []

    assert(len(extracted_logs) == len(extracted_sm_logs))

    for dur_line, sm_line in zip(extracted_logs, extracted_sm_logs):
        kernel_dur.append(float(dur_line.split(',')[1]))
        kernel_sm_efficiency.append(float(sm_line.split(',')[-1]))

    total_sm_efficiency = \
        sum([ d * e for d, e in zip(kernel_dur, kernel_sm_efficiency) ])
    total_kernel_time = sum(kernel_dur)
    
    return total_sm_efficiency / total_kernel_time
