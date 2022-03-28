import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import method1
import method3

def method4_assign(graph, threshold=70, **kwargs):
    wavefronts = []

    while not graph.is_empty():
        wavefronts.append(method1.fill_stage(graph, threshold))
        for sid, id in enumerate(wavefronts[-1]):
            graph.emit_node(id, sid, graph.get_inputs(id))

    method3.insert_barriers(graph, wavefronts)
