def extract_kernel_sm_tf(log_file: str):
    lines = open(log_file).readlines()
    extracted = [ line for line in lines if 'NVIDIA' in line ]
    
    extracted_file = log_file.rstrip('log') + 'extracted.log'
    with open(extracted_file, 'w') as fout:
        for line in extracted:
            fout.write(line)
    return extracted_file

def extract_kernel_tf(log_file: str, extracted_sm_file: str):
    lines = open(log_file).readlines()
    extracted_sm_lines = open(extracted_sm_file).readlines()
    
    i = 0
    extracted = []
    for line in lines:
        if not 'NVIDIA' in line or 'CUDA' in line:
            continue
        expected = extracted_sm_lines[i].rstrip('\n').split('\"')[-2]
        kernel_name = line.rstrip('\n').split('\"')[-2]
        if expected == kernel_name:
            extracted.append(line)
            i += 1
        if i >= len(extracted_sm_lines): 
            break
    
    extracted_file = log_file.rstrip('log') + 'extracted.log'
    with open(extracted_file, 'w') as fout:
        for line in extracted:
            fout.write(line)
    return extracted_file
