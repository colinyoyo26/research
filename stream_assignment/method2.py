
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler
import time
import numpy as np

def get_lower_bound(graph, max_thread_blocks, max_ops):
    graph = copy.deepcopy(graph)
    dot_sum = [0, 0]
    critical_duration = 0
    
    while not graph.is_empty():
        id = graph.ready_nodes()[0]
        inputs = graph.get_inputs(id)
        graph[id].finish_time = graph[id].duration
        if inputs:
            graph[id].finish_time += max([graph[i].finish_time for i in inputs])
        critical_duration = max(critical_duration, graph[id].finish_time)
        dot_sum[0] += graph[id].duration * min(graph[id].grid_size, max_thread_blocks)
        dot_sum[1] += graph[id].duration
        graph.emit_node(id, 0, [])
    
    lbs = (dot_sum[0] / max_thread_blocks, dot_sum[1] / max_ops, critical_duration)
    return max(lbs)

def method2_internal(graph, num_stream):

    max_thread_blocks = int(82 * 16 * 1)
    max_warps = int(82 * 1536 / 32) * 1000000 # unused
    max_registers = int(20992 * 1024 / 4) * 100000 # unused
    max_warps_per_sm = int(1536 * 10 / 32) * 100000 # unused
    max_blocks_per_sm = 16 * 1000000 # unused
    max_memory_throughput = 120 * 100000 # unused
    max_ops = num_stream

    max_time = 2000000
    max_resources = [max_thread_blocks, max_warps, max_registers, 
                    max_warps_per_sm, max_blocks_per_sm, max_memory_throughput, 
                    max_ops]
    num_resources = len(max_resources)

    lb = get_lower_bound(graph, max_thread_blocks, max_ops)

    stream_finish_time = [0] * num_stream
    resources = np.array([[0.] * num_resources] * max_time)

    def get_op_resources(id):
        nonlocal graph
        return [graph[id].grid_size, graph[id].warps, 
                graph[id].registers, graph[id].warps_per_sm, graph[id].blocks_per_sm,
                graph[id].memory, 1]

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
        nonlocal graph, resources, max_resources
        
        op_resources = get_op_resources(id)
        st = max_predecessor_fisish_time(id)
        ft = st + graph[id].duration
        time = st
        while time < ft:
            if np.any(resources[time] + op_resources > max_resources):
                if np.all(resources[st: ft] == 0):
                    break
                st = time + 1
                ft = st + graph[id].duration
            time += 1
        return st

    while not graph.is_empty():
        nodes = graph.ready_nodes()
        id = min(nodes,
            key=lambda x : (get_earliest_start_time(x), -graph[x].grid_size))

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
        resources[st: ft] += get_op_resources(id)

        graph.emit_node(id, sid, graph.get_inputs(id))
    graph[graph.consume_nodes[-1]].stream_id = 0
    return max(stream_finish_time), lb

def method2_assign(graph, **kwargs):
    profiler = Profiler(model_path=kwargs['model_path'])
    best_time = 100000
    b = ()
    for num_stream in list(range(2, 32)) + [100]:
        graph_copy = copy.deepcopy(graph)
        ft, lb = method2_internal(graph_copy, num_stream)
        assert graph_copy.is_empty()
        profiler.set_assigner(graph_copy.get_assigner())
        time = profiler.get_profile_time()
        
        if time < best_time:
            b = (num_stream, time, ft, ft / lb)
            best_graph = graph_copy
            best_time = time
            best = num_stream
    print(b)
    graph.assign(best_graph)    
