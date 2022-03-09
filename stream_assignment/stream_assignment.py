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

# wavefront
def wavefront_assign(json_dict, graph, assigner, extracted_file=''):
    wait_list = []
    emit_order = 0

    # BFS
    while not graph.is_empty():
        curLevel = graph.ready_nodes()
        size = len(curLevel)
        for i in range(size):
            cur_id = curLevel[i]
            graph.consume(cur_id)
            assigner.set_stream_id(cur_id, i)
            assigner.set_emit_order(cur_id, emit_order)
            assigner.set_wait_list(cur_id, wait_list)
            emit_order += 1
        wait_list = curLevel

def default_assign(json_dict, graph, assigner, extracted_file):
    num_node = len(json_dict['nodes'])
    cnt = 0
    for i in range(num_node):
        if json_dict['nodes'][i]['op'] == 'tvm_op':
            assigner.set_stream_id(i, 0)
            assigner.set_wait_list(i, [])
            assigner.set_emit_order(i, cnt)
            cnt += 1

# profiled based
def test_assign(json_dict, graph, assigner, extracted_file):
    kernel_info = nvlog.info.get_kernel_info(extracted_file)
    print(kernel_info)

def assign_stream(json_dict, assign_func, extracted_file):
    num_node = len(json_dict['nodes'])

    graph = Graph(json_dict)
    assigner = Assigner(json_dict)

    assign_func(json_dict, graph, assigner, extracted_file)
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
