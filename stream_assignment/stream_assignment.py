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
from method1 import method1_assign, method1_stage_assign
from method2 import method2_assign
from method3 import method3_assign
from method4 import method4_assign
from method5 import method5_assign
from method6 import method6_assign

def default_assign(graph):
    while not graph.is_empty():
        for id in graph.ready_nodes():
            graph.emit_node(id, 0, [])

# wavefront
def wavefront_assign(graph):
    method1_assign(graph, 10000)

# wavefront / stage
def wavefront_stage_assign(graph):
    method1_stage_assign(graph, 10000)

def assign_stream(json_dict, assign_func, extracted_file):
    if assign_func == default_assign:
        kernel_info = defaultdict(lambda : [0, 0])
    else:
        kernel_info = nvlog.info.get_kernel_info(extracted_file)
    graph = Graph(json_dict, kernel_info)

    assign_func(graph)
    graph.save_assignment()

def get_assign_method(method):
    methods = {'wavefront': wavefront_assign,
               'wavefront_stage': wavefront_stage_assign,
               'method1': method1_assign,
               'method1_stage': method1_stage_assign,
               'method2': method2_assign,
               'method3': method3_assign,
               'method4': method4_assign,
               'method5': method5_assign,
               'method6': method6_assign}
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
