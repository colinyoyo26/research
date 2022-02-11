import os
import json
import argparse
import copy
from collections import defaultdict

# `id` should wait id in `wait_list` 
def wait(id, wait_list, assignment):
    assignment[id][1] = copy.deepcopy(wait_list)
    

def buildGraph(json_dict):
    num_node = len(json_dict['nodes'])
    adjList = [[] for _ in range(num_node)]
    inDegree = [0] * num_node
    for cur_id in range(num_node):
        inputs = json_dict['nodes'][cur_id]['inputs']
        inDegree[cur_id] = len(inputs)
        for input_id, _, _ in inputs:
            adjList[input_id].append(cur_id)
    return adjList, inDegree

def default_assign(json_dict, adjList, inDegree):
    #inDegree = copy.deepcopy(inDegree)
    arg_nodes = json_dict['arg_nodes']
    num_node = len(json_dict['nodes'])
    curLevel = copy.deepcopy(arg_nodes)

    assignment = [[] for _ in range(num_node)] # index: node_id, content: [stream_id, wait_events (list of node id)]
    wait_list = []
    
    # BFS
    while len(curLevel):
        size = len(curLevel)
        nextLevel = []
        for i in range(size):
            cur_id = curLevel[i]
            for output_id in adjList[cur_id]:
                inDegree[output_id] -= 1
                if inDegree[output_id] == 0:
                    assignment[output_id] = [len(nextLevel), []]
                    nextLevel.append(output_id)
                    wait(output_id, wait_list, assignment)
        curLevel = nextLevel
        wait_list = curLevel
    return assignment

def get_kernel_id(json_dict):
    num_node = len(json_dict['nodes'])
    kernel_id = [-1] * num_node # -1 for null node
    kernel_node_cnt = 0
    for cur_id in range(num_node):
        key = 'attr'
        if not key in json_dict['nodes'][cur_id].keys():
            key = 'attrs'
        if key in json_dict['nodes'][cur_id].keys():
            kernel_id[cur_id] = kernel_node_cnt
            kernel_node_cnt += 1
    return kernel_id

def assign_stream(json_dict, assign_func):
    num_node = len(json_dict['nodes'])
    adjList, inDegree = buildGraph(json_dict)
    
    kernel_id = get_kernel_id(json_dict)

    assignment = assign_func(json_dict, adjList, inDegree)
    
    res = {"assignment": []}

    for cur_id in range(num_node):
        assert inDegree[cur_id] == 0
        key = 'attr'
        if not key in json_dict['nodes'][cur_id].keys():
            key = 'attrs'
        assert key in json_dict['nodes'][cur_id].keys() and kernel_id[cur_id] != -1 or \
               key not in json_dict['nodes'][cur_id].keys() and kernel_id[cur_id] == -1
        if kernel_id[cur_id] != -1:
            func_name = json_dict['nodes'][cur_id][key]['func_name']
            kid = kernel_id[cur_id]
            assert -1 not in assignment[cur_id][1]
            res['assignment'].append({'func_name': func_name, # func_name for  verification
                                      'stream_id': assignment[cur_id][0],
                                      'wait_list': [kernel_id[id] for id in assignment[cur_id][1]]}) 
    return res    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    res = assign_stream(json_dict, default_assign)
    res_json = json.dumps(res, indent=2)

    path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
    #path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    open(path, 'w').write(res_json)
