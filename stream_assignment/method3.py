import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from profiler import Profiler

def insert_barriers(graph, wavefronts):
    profiler = Profiler()
    min_time = 100000
    prev_wave = []
    for i, wave in enumerate(wavefronts):
        for id in wave:
            graph.set_wait_list(id, prev_wave)
        profiler.set_assigner(graph.get_assigner())
        time = profiler.get_profile_time()

        if time > min_time:
            for id in wave:
                graph.set_wait_list(id, graph.get_inputs(id))
        min_time = min(min_time, time)
        prev_wave = wave

def method3_assign(graph):
    wavefronts = []

    while not graph.is_empty():
        wavefronts.append(graph.ready_nodes())
        for sid, id in enumerate(wavefronts[-1]):
            graph.emit_node(id, sid, graph.get_inputs(id))

    insert_barriers(graph, wavefronts)
