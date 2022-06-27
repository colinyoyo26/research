
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import numpy as np
from collections import defaultdict

def get_lower_bound(graph, max_resources, max_ops):
    graph = copy.deepcopy(graph)
    dot_sum = [0] * len(max_resources)
    critical_duration = 0
    
    while not graph.is_empty():
        id = graph.ready_nodes()[0]
        inputs = graph.get_inputs(id)
        graph[id].finish_time = graph[id].duration
        if inputs:
            graph[id].finish_time += max([graph[i].finish_time for i in inputs])
        critical_duration = max(critical_duration, graph[id].finish_time)
        
        op_resources = get_op_resources(id, graph)
        for i, op_res in enumerate(op_resources):
            dot_sum[i] += graph[id].duration * op_res
        graph.emit_node(id, 0, [])
    
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

def method2_internal(graph, num_stream):

    max_resident_thread_blocks = int(82 * 16 * 1)
    max_ops = num_stream

    max_time = 2000000
    max_resources = [max_resident_thread_blocks, max_ops]
    num_resources = len(max_resources)

    lb = get_lower_bound(graph, max_resources, max_ops)

    stream_finish_time = [0] * num_stream
    resources = np.array([[0.] * num_resources] * max_time)
    start_times = defaultdict(lambda : -1)

    def get_latest_inputs(id):
        nonlocal graph
        inputs = graph.get_inputs(id)
        if not inputs:
            return []
        mx_ft = max([graph[i].finish_time for i in inputs])
        return [i for i in inputs if graph[i].finish_time == mx_ft]
    
    def max_predecessor_fisish_time(id):
        nonlocal graph
        latest_inputs = get_latest_inputs(id)
        if not latest_inputs:
            return 0
        return graph[latest_inputs[0]].finish_time

    def get_earliest_start_time(id):
        nonlocal graph, resources, max_resources, start_times
        
        op_resources = get_op_resources(id, graph)
        if start_times[id] == -1:
            start_times[id] = max_predecessor_fisish_time(id)
        st = start_times[id]
        ft = st + graph[id].duration
        time = st
        while time < ft:
            if np.any(resources[time] + op_resources > max_resources):
                assert not np.all(resources[st: ft] == 0)
                st = time + 1
                ft = st + graph[id].duration
            time += 1
        start_times[id] = st
        return st

    while not graph.is_empty():
        nodes = graph.ready_nodes()
        id = min(nodes,
            key=lambda x : (get_earliest_start_time(x), -get_op_resources(x, graph)[0]))

        latest_inputs = get_latest_inputs(id)
        candidates = [graph[i].stream_id for i in latest_inputs]

        st = get_earliest_start_time(id)

        sid = min(enumerate(stream_finish_time),
                  key=lambda x :  (max(x[1], st),
                                  x[0] not in candidates,
                                  x[1] == 0,
                                  x[0]))[0]
        ft = st + graph[id].duration
        graph[id].finish_time = stream_finish_time[sid] = ft 
        resources[st: ft] += get_op_resources(id, graph)

        graph.emit_node(id, sid, graph.get_inputs(id))
    graph[graph.consume_nodes[-1]].stream_id = 0
    return max(stream_finish_time) / 1e3, lb / 1e3

def method2_assign(graph, **kwargs):
    best_time = 100000000
    b = []
    for num_stream in range(7, 12):
        graph_copy = copy.deepcopy(graph)
        ft, lb = method2_internal(graph_copy, num_stream)
        assert graph_copy.is_empty()
        time = graph_copy.get_latency()
        print(num_stream, time)
        if time < best_time:
            b = [num_stream, time, ft, ft / lb]
            best_graph = graph_copy
            best_time = time
            best = num_stream
    graph.assign(best_graph)
    b[0] = max([graph[id].stream_id for id in graph.topo_order]) + 1
    return {'max_ops': b[0], 'time': b[1], 'makespan': b[2], 'ratio': b[3]}
