import os
import sys
import json
import copy
from collections import defaultdict

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import nvlog
from . import Graph
from baseline import default_assign, bfs_assign
from method2 import method2_assign
from ios import ios_assign

def doit(json_dict, tvm_cache, method, log_file, res_file, res_entry):
    assign_func = get_assign_func(method)
    kernel_info=defaultdict(lambda: defaultdict(lambda: 1))
    if assign_func != default_assign:
        kernel_info = nvlog.info.get_kernel_info(log_file)
    graph = Graph(tvm_cache, kernel_info)
    res_dict = assign_func(graph)

    if res_file:
        save_res(res_file, res_entry, res_dict, graph)
    graph.save_assignment()

def save_res(res_file, res_entry, res_dict, graph):
    try:
        res_json = json.load(open(res_file, 'r'))
    except:
        res_json = {}
    if not res_entry in res_json.keys():
        res_json[res_entry] = {}
    assigner = graph.get_assigner()
    assigner.optimize()
    res_json[res_entry]['synchronizations'] = sum([len(a['wait_list']) for a in assigner.res['assignment']]) 
    res_json[res_entry]['max_ops'] = max([a['stream_id'] + 1 for a in assigner.res['assignment']]) 
    res_json[res_entry]['time(ms)'] = graph.get_latency()
    for key, val in res_dict.items():
        res_json[res_entry][key] = val
    s = json.dumps(res_json, indent=2)
    open(res_file, 'w').write(s)

def get_assign_func(method):
    methods = {'bfs': bfs_assign,
               'method2': method2_assign,
               'ios': ios_assign}
    assign_method = methods.get(method)
    if not assign_method:
        assign_method = default_assign
    return assign_method

def schedule(log_file, tvm_cache, res_entry, res_file=None, method='default'):
    json_path = tvm_cache + '.json'
    f = open(json_path)
    json_dict = json.load(f)
    doit(json_dict, tvm_cache, method, log_file, res_file, res_entry)

    # make storage to be correct in a brute force way
    for i in range(len(json_dict['attrs']['storage_id'][1])):
        json_dict['attrs']['storage_id'][1][i] = i
    s = json.dumps(json_dict, indent=2)
    open(json_path, 'w').write(s)
