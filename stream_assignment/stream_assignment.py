import os
import sys
import json
import argparse
import copy
from collections import defaultdict

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import nvlog
from assigner import Assigner
from graph import Graph

def default_assign(json_dict, graph, assigner):
    num_node = len(json_dict['nodes'])
    cnt = 0
    for i in range(num_node):
        if json_dict['nodes'][i]['op'] == 'tvm_op':
            assigner.set_stream_id(i, 0)
            assigner.set_wait_list(i, [])
            assigner.set_emit_order(i, cnt)
            cnt += 1

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
    
# profiled based
def test_assign(json_dict, graph, assigner, threshold=140):
    emit_order = 0
    wait_list = []
    # BFS
    while not graph.is_empty():
        node_ids = fill_stage(graph, threshold)    
        for i in range(len(node_ids)):
            id = node_ids[i]
            graph.consume(id)
            assigner.set_wait_list(id, wait_list)
            assigner.set_stream_id(id, i)
            assigner.set_emit_order(id, emit_order)
            emit_order += 1
        wait_list = node_ids

# wavefront
def wavefront_assign(json_dict, graph, assigner):
    test_assign(json_dict, graph, assigner, 10000)


def assign_stream(json_dict, assign_func, extracted_file):
    kernel_info = nvlog.info.get_kernel_info(extracted_file)
    graph = Graph(json_dict, kernel_info)
    assigner = Assigner(json_dict)

    assign_func(json_dict, graph, assigner)
    assigner.save_assignment()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    parser.add_argument('--extracted_file', type=str, default='', help='tvm json file path')
    parser.add_argument('--method', type=str, default='default')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    extracted_file = args['extracted_file']
    method = args['method']
    assign_method = default_assign
    if method == 'wavefront':
        assign_method = wavefront_assign
    elif method == 'test':
        assign_method = test_assign

    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    assign_stream(json_dict, assign_method, extracted_file)
