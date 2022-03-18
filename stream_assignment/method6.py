import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler

def method6_assign(graph):
    num_stream = 6
    profiler = Profiler()

    while not graph.is_empty():
        id = graph.ready_nodes()[0]
        graph.emit_node(id, 0, graph.get_inputs(id))
        
        sid_to_assign = 0
        finish_time = 100000
        for sid in range(num_stream):
            graph.set_stream_id(id, sid)
            profiler.set_assigner(graph.get_assigner())
            t = profiler.get_profile_time()
            if t < finish_time:
                sid_to_assign = sid
                finish_time = t
        graph.set_stream_id(id, sid_to_assign)
