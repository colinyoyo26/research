def process_log(extracted_file: str):
    lines = open(extracted_file).readlines()

    utilization_varieties = []
    for line in lines:
        _, stream_id, start_time, duration, sm_efficiency, achieved_occupacy = line.split('$')
        start_time = float(start_time)
        end_time = start_time + float(duration)
        utilization = float(sm_efficiency) * float(achieved_occupacy)
        utilization_varieties.append((start_time, utilization))
        utilization_varieties.append((end_time, -utilization))
    
    utilization_varieties = sorted(utilization_varieties)
    utilization = 0.
    weighted_utilization = 0.
    total_time = 0.
    overlaps = 0
    prev_time = utilization_varieties[0][0]
    for time, variety in utilization_varieties:
        if overlaps > 0:
            weighted_utilization += utilization * (time - prev_time)
            total_time += time - prev_time
        overlaps += 1 if variety > 0 else -1
        utilization += variety 
        prev_time = time

    return weighted_utilization / total_time, total_time
