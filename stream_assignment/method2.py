import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import method1
import copy
import heapq

def fill_stage(graph, max_utilization, max_duration):
    graph_copy = copy.deepcopy(graph)
    nodes = method1.fill_stage(graph, max_utilization)
    if len(nodes) == 1:
        return [nodes]
    stream_info = [[graph.get_duration(id), 
                    graph.get_utilization(id),
                    [id]] 
                    for id in nodes]
    total_utilization = sum([graph.get_utilization(id) for id in nodes])
    for id in nodes:
        graph_copy.emit_node(id, 0, [])

    def can_assign_to_stream(id, info):
        nonlocal graph, total_utilization
        dur, util, ids = info
        for input_id in graph.get_inputs(id):
            # check dependency, duration, utilization
            if (not (graph.is_emitted(input_id) or input_id in ids)) or \
               (graph.get_duration(id) + dur > max_duration) or \
               (max(graph.get_utilization(id), util) - util + total_utilization > max_utilization):
                return False 
        return True

    heapq.heapify(stream_info)
    has_candidate = True
    
    while has_candidate:
        has_candidate = False
        info = heapq.heappop(stream_info)
        for id in graph_copy.ready_nodes():
            if can_assign_to_stream(id, info):
                new_utilization = max(info[1], graph.get_utilization(id))
                total_utilization += new_utilization - info[1] 
                info[0] += graph.get_duration(id)
                info[1] = new_utilization
                info[2].append(id)
                graph_copy.emit_node(id, 0, [])
                has_candidate = True
        heapq.heappush(stream_info, info)
                
    return [info[2] for info in stream_info]

# profiled based / non stage
def method2_assign(graph, max_utilization=100, max_duration=70):
    wait_list = []
    while not graph.is_empty():
        node_ids = fill_stage(graph, max_utilization, max_duration)
        for i, ids in enumerate(node_ids):
            for id in ids:
                graph.emit_node(id, i, wait_list)
        wait_list = [ids[-1] for ids in node_ids]
