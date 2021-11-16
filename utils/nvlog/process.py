def process_log(extracted_file: str):
    lines = open(extracted_file).readlines()

    active_count = 0
    total_time = 0
    for line in lines:
        duration = float(line.split('$')[1])
        sm_efficiency = float(line.split('$')[2])
        achieved_occupacy = float(line.split('$')[3])
        active_count = active_count + duration * sm_efficiency * achieved_occupacy
        total_time = total_time + duration
    
    return active_count / total_time
