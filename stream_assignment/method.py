
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler

def method_internal(graph, num_stream):
    stream_finish_time = [0] * num_stream
    
    def get_latest_inputs(id):
        nonlocal graph
        inputs = graph.get_inputs(id)
        if not inputs:
            return []
        mx_ft = max([graph[i].finish_time for i in inputs])
        return [i for i in inputs if graph[i].finish_time == mx_ft]
    
    def get_start_time(id):
        nonlocal graph
        latest_inputs = get_latest_inputs(id)
        if not latest_inputs:
            return 0
        return graph[latest_inputs[0]].finish_time

    while not graph.is_empty():
        nodes = graph.ready_nodes()
        id = min(nodes,
            key=lambda x : (get_start_time(x), -graph[x].duration))
        latest_inputs = get_latest_inputs(id)
        candidates = [graph[i].stream_id for i in latest_inputs]

        st = get_start_time(id)

        sid = min(enumerate(stream_finish_time), 
                  key=lambda x : (max(x[1], st),
                                  x[0] not in candidates,
                                  x[1]))[0]

        finish_time = max(st, stream_finish_time[sid]) \
            + graph.get_duration(id)

        graph[id].finish_time = stream_finish_time[sid] = finish_time 
        graph.emit_node(id, sid, graph.get_inputs(id))
    graph[graph.consume_nodes[-1]].stream_id = 0

def method_assign(graph, **kwargs):
    profiler = Profiler(model_path=kwargs['model_path'])
    best_time = 100000

    for num_stream in range(1,33, 1):
        graph_copy = copy.deepcopy(graph)
        approx = method_internal(graph_copy, num_stream)
        assert graph_copy.is_empty()
        profiler.set_assigner(graph_copy.get_assigner())
        time = profiler.get_profile_time()
        if time < best_time:
            best_graph = graph_copy
            best_time = time
            best = num_stream
    graph.assign(best_graph)    
