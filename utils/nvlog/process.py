def process_log(extracted_file: str):
    lines = open(extracted_file).readlines()

    total_active_time = 0
    total_time = 0
    for line in lines:
        dur = float(line.split('$')[1])
        sm_efficiency = float(line.split('$')[2])
        total_active_time = total_active_time + dur * sm_efficiency
        total_time = total_time + dur
    
    return total_active_time / total_time
