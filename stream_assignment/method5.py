
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler

def method5_internal(graph, num_stream):
    stream_finish_time = [0] * num_stream

    def node_earliest_start_time(id):
        nonlocal graph
        inputs = graph.get_inputs(id)
        if not inputs:
            return 0
        return max([graph[i].finish_time for i in inputs])

    while not graph.is_empty():
        nodes = graph.ready_nodes()
        id = min(nodes,
            key=lambda x : (node_earliest_start_time(x), -graph.get_duration(x)))
        st = node_earliest_start_time(id)
        
        sid = min(enumerate(stream_finish_time), 
            key=lambda x : (max(x[1], st), -x[1]))[0]
        finish_time = max(st, stream_finish_time[sid]) \
            + graph.get_duration(id)
        graph[id].finish_time = stream_finish_time[sid] = finish_time 
        graph.emit_node(id, sid, graph.get_inputs(id))

def method5_assign(graph):
    profiler = Profiler()
    best_time = 100000

    for num_stream in range(1, 11, 1):
        graph_copy = copy.deepcopy(graph)
        method5_internal(graph_copy, num_stream)
        assert graph_copy.is_empty()
        profiler.set_assigner(graph_copy.get_assigner())
        time = profiler.get_profile_time()

        if time < best_time:
            best_graph = graph_copy
            best_time = time
    graph.assign(best_graph)    
