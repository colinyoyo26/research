import os
import sys
import json
import argparse
import copy
from collections import defaultdict
import heapq

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import nvlog
from graph import Graph

def default_assign(graph):
    while not graph.is_empty():
        for id in graph.ready_nodes():
            graph.emit_node(id, 0, [])

def fill_stage(graph, threshold):
    curLevel = graph.ready_nodes()
    utilizations = [int(graph.get_utilization(id)) for id in curLevel]
    if max(utilizations) >= threshold:
        return [curLevel[max(enumerate(utilizations), key=lambda x : x[1])[0]]]

    n = len(curLevel)
    prev_dp = [0] * (threshold + 1)
    record = [[False] * (threshold + 1) for _ in range(n)]
    for i in range(1, n + 1, 1):
        cur_dp = [0] * (threshold + 1)
        # can't have 0 utilization
        w = utilizations[i - 1] = max(utilizations[i - 1], 1)
        for j in range(threshold + 1):
            cur_dp[j] = prev_dp[j]
            if j >= w and w + prev_dp[j - w] > cur_dp[j]:
                cur_dp[j] = w + prev_dp[j - w]
                record[i - 1][j] = True
        prev_dp = cur_dp
    
    assert prev_dp[threshold] > 0 or print(utilizations)
    result = []
    remain = threshold
    for i in range(n - 1, -1, -1):
        if record[i][remain]:
            result.append(curLevel[i])
            remain -= utilizations[i]
    assert threshold - remain == prev_dp[threshold] or print(threshold - remain, prev_dp[threshold])
    return result

# profiled based / non stage
def method1_assign(graph, threshold=100):
    while not graph.is_empty():
        node_ids = fill_stage(graph, threshold)    
        for i, id in enumerate(node_ids):
            graph.emit_node(id, i, graph.get_inputs(id))
        

# profile based / stage 
def method1_stage_assign(graph, threshold=100):
    wait_list = []
    while not graph.is_empty():
        node_ids = fill_stage(graph, threshold)    
        for i, id in enumerate(node_ids):
            graph.emit_node(id, i, wait_list)
        wait_list = node_ids

# wavefront
def wavefront_assign(graph):
    method1_assign(graph, 10000)

# wavefront / stage
def wavefront_stage_assign(graph):
    method1_stage_assign(graph, 10000)

def assign_stream(json_dict, assign_func, extracted_file):
    kernel_info = nvlog.info.get_kernel_info(extracted_file)
    graph = Graph(json_dict, kernel_info)

    assign_func(graph)
    graph.save_assignment()

def get_assign_method(method):
    methods = {'wavefront': wavefront_assign,
               'wavefront_stage': wavefront_stage_assign,
               'method1': method1_assign,
               'method1_stage': method1_stage_assign}
    assign_method = methods.get(method)
    if not assign_method:
        assign_method = default_assign
    return assign_method

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    parser.add_argument('--extracted_file', type=str, default='', help='tvm json file path')
    parser.add_argument('--method', type=str, default='default')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    extracted_file = args['extracted_file']
    method = args['method']
    assign_method = get_assign_method(method)

    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    assign_stream(json_dict, assign_method, extracted_file)

    # make storage to be correct in a brute force way
    for i in range(len(json_dict['attrs']['storage_id'][1])):
        json_dict['attrs']['storage_id'][1][i] = i
    s = json.dumps(json_dict, indent=2)
    open(json_path, 'w').write(s)
