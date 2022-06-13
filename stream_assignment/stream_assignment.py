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
from graph import Graph
from baseline import default_assign, bfs_assign
from method import method_assign
from method2 import method2_assign
from method3 import method3_assign

def assign_stream(json_dict, model_path, assign_func, log_file):
    kernel_info = defaultdict(lambda : {'duration': 0, 'grid_size': 0, 'block_size':0,
                                        'threads': 0, 'registers_per_thread': 0, 
                                        'warps_per_sm': 0,
                                        'memory': 0})
    if assign_func != default_assign:
        kernel_info = nvlog.info.get_kernel_info(log_file)
    graph = Graph(json_dict, kernel_info)

    assign_func(graph, model_path=model_path)
    graph.save_assignment()

def get_assign_method(method):
    methods = {'bfs': bfs_assign,
               'method': method_assign,
               'method2': method2_assign,
               'method3': method3_assign}
    assign_method = methods.get(method)
    if not assign_method:
        assign_method = default_assign
    return assign_method

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    parser.add_argument('--log_file', type=str, default='')
    parser.add_argument('--method', type=str, default='default')
    parser.add_argument('--model_path', type=str, default='')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    log_file = args['log_file']
    method = args['method']
    model_path = args['model_path']
    assign_method = get_assign_method(method)

    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    assign_stream(json_dict, model_path, assign_method, log_file)

    # make storage to be correct in a brute force way
    for i in range(len(json_dict['attrs']['storage_id'][1])):
        json_dict['attrs']['storage_id'][1][i] = i
    s = json.dumps(json_dict, indent=2)
    open(json_path, 'w').write(s)
