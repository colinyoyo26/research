import sys
import os
import copy
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler

def get_partition(graph):
    # TODO
    graph_copy = copy.deepcopy(graph)
    partition = [[]]
    while not graph_copy.is_empty():
        wave = graph_copy.ready_nodes()
        
        for id in wave:
            partition[-1].append(id)
            graph_copy.emit_node(id, 0, [])
        if len(partition[-1]) > 30:
            partition.append([])    
    return partition

def method6_internal(graph, stream_idx, stream_finish_time, candidates):
    candidates = set(candidates)

    def node_earliest_start_time(id):
        nonlocal graph
        inputs = graph.get_inputs(id)
        if not inputs:
            return 0
        return max([graph[i].finish_time for i in inputs])

    for _ in candidates:
        nodes = [id for id in graph.ready_nodes() if id in candidates]
        id = min(nodes,
            key=lambda x : (node_earliest_start_time(x), graph[x].duration))
        st = node_earliest_start_time(id)
        
        sid = min(stream_idx, 
            key=lambda x : (max(stream_finish_time[x], st), 
                            -stream_finish_time[x]))
        finish_time = max(st, stream_finish_time[sid]) \
            + graph.get_duration(id)
        graph[id].finish_time = stream_finish_time[sid] = finish_time 
        graph.emit_node(id, sid, graph.get_inputs(id))

def profile_best(graph, partition):
    profiler = Profiler()
    max_stream = 10
    stream_finish_time = [0] * max_stream

    def choose_stream_idx():
        # TODO
        nonlocal max_stream, stream_finish_time
        idx = list(range(max_stream))
        random.shuffle(idx)
        return idx

    for candidates in partition:
        best_time = 100000
        stream_idx = choose_stream_idx()
        for num_stream in range(1, max_stream, 1):
            graph_copy = copy.deepcopy(graph)
            
            sft = copy.deepcopy(stream_finish_time)

            method6_internal(graph_copy, stream_idx[: num_stream], sft, candidates)
            profiler.set_assigner(graph_copy.get_assigner())
            time = profiler.get_profile_time()
            if time < best_time:
                best_stream_finish_time = sft
                best_graph = graph_copy
                best_time = time
        stream_finish_time = best_stream_finish_time
        graph.assign(best_graph)

def method6_assign(graph):
    partition = get_partition(graph)
    profile_best(graph, partition)
