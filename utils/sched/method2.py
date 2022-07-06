
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import numpy as np
from collections import defaultdict

def get_lower_bound(graph, max_resources):
    dot_sum = [0] * len(max_resources)
    critical_duration = 0
    for id in graph.get_topo():
        inputs = graph.get_inputs(id)
        graph[id].finish_time = graph[id].duration
        if inputs:
            graph[id].finish_time += max([graph[i].finish_time for i in inputs])
        critical_duration = max(critical_duration, graph[id].finish_time)
        
        op_resources = get_op_resources(id, graph)
        for i, op_res in enumerate(op_resources):
            dot_sum[i] += graph[id].duration * op_res
    
    lbs = [ds / mr for ds, mr in zip(dot_sum, max_resources)] + [critical_duration]
    return max(lbs)

def get_op_resources(id, graph):
    num_sm = 82
    max_blocks_per_sm = 16
    max_registers_per_sm = 64 *  1024
    max_warps_per_sm = 48
    max_shared_mem_per_sm = 164 * 1024 # bytes

    blocks_per_wave = min(graph[id].grid_size, 
        min([max_blocks_per_sm, 
        max_registers_per_sm // max(1, graph[id].registers_per_block),
        max_warps_per_sm // graph[id].warps_per_block,
        max_shared_mem_per_sm // max(1, graph[id].shr_mem_per_block)]) * 82)
    return [blocks_per_wave, 1]

def critical_distance(graph):
    cd = {}
    tc = graph.get_transitive_closure(graph.get_topo())

    for id in graph.get_topo():
        cd[id] = sum([graph[i].duration for i in tc[id]])
    return cd

def critical_length(graph):
    cl = {}
    res = 0
    for id in graph.get_topo():
        cl[id] = graph[id].duration
        inputs = graph[id].inputs
        if inputs:
            cl[id] += max([cl[i] for i in inputs])
        res = max(res, cl[id])
    return res

def method2_internal(graph, num_stream, cd):
    max_resident_thread_blocks = int(82 * 16 * 1)
    max_ops = num_stream

    max_resources = [max_resident_thread_blocks, max_ops]
    num_resources = len(max_resources)

    lb = get_lower_bound(graph, max_resources)
    stream_finish_time = [0] * num_stream
    
    s = {}
    resource_variations = defaultdict(lambda: np.array([0.] * num_resources))
    start_time = 0

    def resource_usage_at_time(time):
        nonlocal resource_variations, num_resources
        usage = np.array([0.] * num_resources)
        for t, variation in resource_variations.items():
            if t <= time:
                usage += variation
        assert np.all(usage >= 0) and np.all(usage <= max_resources)
        return usage
 
    def operators_can_start_at_time(time, R):
        nonlocal resource_variations, max_resources, s, graph
        usage = resource_usage_at_time(time)
        S = []
        
        for id in R:
            if not id in s.keys():
                inputs = graph[id].inputs
                s[id] = 0 if not inputs else max([s[i] + graph[i].duration for i in inputs])
            if s[id] <= time and np.all(get_op_resources(id, graph) + usage <= max_resources):
                S.append(id)
        return S

    def get_latest_inputs(id):
        nonlocal graph, s
        inputs = graph.get_inputs(id)
        if not inputs:
            return []
        mx_ft = max([s[i] + graph[i].duration for i in inputs])
        return [i for i in inputs if s[i] + graph[i].duration == mx_ft]

    while not graph.is_empty():
        S = operators_can_start_at_time(start_time, graph.ready_nodes())
        if not S:
            start_time = min([t for t in resource_variations.keys() if t > start_time])
        else:
            id = max(S, key=lambda x: cd[x])  # selection rule
            s[id] = start_time
            op_resources = get_op_resources(id, graph)
            resource_variations[start_time] += op_resources
            resource_variations[start_time + graph[id].duration] -= op_resources

            streams_cadidates = set([graph[i].stream_id for i in get_latest_inputs(id)])

            sid = min(enumerate(stream_finish_time),
                    key=lambda x :  (max(x[1], start_time),
                    x[0] not in streams_cadidates,
                    x[1] == 0,
                    x[0]))[0]
            assert stream_finish_time[sid] <= start_time
            stream_finish_time[sid] = start_time + graph[id].duration
            graph.emit_node(id, sid, graph.get_inputs(id))
    graph[graph.consume_nodes[-1]].stream_id = 0
    return max(stream_finish_time) / 1e3, lb / 1e3

def method2_assign(graph, **kwargs):
    best_time = 100000000
    best = []
    cd = critical_distance(graph)
    for num_stream in range(1, 65):
        ft, lb = method2_internal(graph, num_stream, cd)
        assert graph.is_empty()
        time = graph.get_latency()
        graph.reset()
        if time < best_time:
            best = [num_stream, time, ft, ft / lb]
            best_time = time

    method2_internal(graph, best[0], cd)
    best[0] = max([graph[id].stream_id for id in graph.get_topo()]) + 1
    return {'makespan': best[2], 'ratio': best[3], 'critical': critical_length(graph) / 1e3}
