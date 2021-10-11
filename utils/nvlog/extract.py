def extract_kernel_tf(log_file: str):
    lines = open(log_file).readlines()

    is_valid = lambda line : 'NVIDIA' in line and not 'CUDA' in line
    extracted = [ line for line in lines if is_valid(line) ]

    extracted_file = log_file.rstrip('log') + 'extracted.log'
    with open(extracted_file, 'w') as fout:
        for line in extracted:
            fout.write(line)
    return extracted_file
