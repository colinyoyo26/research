import os
import json
import argparse
from collections import deque
from collections import defaultdict


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
    arg_nodes = json_dict['arg_nodes']
    num_node = len(json_dict['nodes'])
    curLevel = deque(arg_nodes)
    assignment = [-1] * num_node
    while len(curLevel):
        size = len(curLevel)
        for i in range(size):
            cur_id = curLevel.popleft()
            assignment[cur_id] = i
            for output_id in adjList[cur_id]:
                inDegree[output_id] -= 1
                if inDegree[output_id] == 0:
                    curLevel.append(output_id)
    return assignment

def assign_stream(json_dict, assign_func):
    num_node = len(json_dict['nodes'])
    adjList, inDegree = buildGraph(json_dict)

    assignment = assign_func(json_dict, adjList, inDegree)
    
        
    res = defaultdict(lambda: [])
    for cur_id in range(num_node):
        key = 'attr'
        if not key in json_dict['nodes'][cur_id].keys():
            key = 'attrs'
        if key in json_dict['nodes'][cur_id].keys():
            func_name = json_dict['nodes'][cur_id][key]['func_name']
            res[func_name].append(assignment[cur_id])
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
