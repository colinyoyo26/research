import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler
import method1

def insert_barriers(graph, wavefronts):
    profiler = Profiler()
    min_time = 100000
    stream_ends = []
    for i, wave in enumerate(wavefronts):
        for id in wave:
            graph.set_wait_list(id, stream_ends)
        profiler.set_assigner(graph.get_assigner())
        time = profiler.get_profile_time()

        if time > min_time:
            for id in wave:
                graph.set_wait_list(id, graph.get_inputs(id))
        min_time = min(min_time, time)

        for id in wave:
            method1.update_stream_ends(graph, id, stream_ends)

def method3_assign(graph, **kwargs):
    wavefronts = []

    while not graph.is_empty():
        wavefronts.append(graph.ready_nodes())
        for sid, id in enumerate(wavefronts[-1]):
            graph.emit_node(id, sid, graph.get_inputs(id))

    insert_barriers(graph, wavefronts)
