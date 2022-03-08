import os
import sys
import json
import argparse
import copy
from collections import defaultdict

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
from utils import nvlog

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

# wavefront
def wavefront_assign(json_dict, adjList, inDegree, extracted_file=''):
    #inDegree = copy.deepcopy(inDegree)
    arg_nodes = json_dict['arg_nodes']
    num_node = len(json_dict['nodes'])
    curLevel = copy.deepcopy(arg_nodes)

    assignment = [[] for _ in range(num_node)]
    wait_list = []
    emit_order = 0

    # BFS
    while len(curLevel):
        size = len(curLevel)
        nextLevel = []
        for i in range(size):
            cur_id = curLevel[i]
            for output_id in adjList[cur_id]:
                inDegree[output_id] -= 1
                if inDegree[output_id] == 0:
                    assignment[output_id] = [len(nextLevel), [], emit_order]
                    emit_order += 1
                    nextLevel.append(output_id)
                    wait(output_id, wait_list, assignment)
        curLevel = nextLevel
        wait_list = curLevel
    return assignment

def default_assign(json_dict, adjList, inDegree, extracted_file):
    num_node = len(json_dict['nodes'])
    assignment = [[] for _ in range(num_node)]
    cnt = 0
    for i in range(num_node):
        if json_dict['nodes'][i]['op'] == 'tvm_op':
            assignment[i]= [0, [], cnt]
            cnt += 1
    return assignment

# profiled based
def test_assign(json_dict, adjList, inDegree, extracted_file):
    kernel_info = nvlog.info.get_kernel_info(extracted_file)
    print(kernel_info)

def assign_stream(json_dict, assign_func, extracted_file):
    num_node = len(json_dict['nodes'])
    adjList, inDegree = buildGraph(json_dict)
    num_tvmop = sum([1 for i in json_dict['nodes'] if i['op'] == 'tvm_op'])


    # index: node_id, content: [stream_id, wait_events (list of node id), emit order]
    assignment = assign_func(json_dict, adjList, inDegree, extracted_file)

    res = {"assignment": [{}] * num_tvmop}
    order = {'emit_order': []}
    i = 0
    for cur_id in range(num_node):
        #assert inDegree[cur_id] == 0
        key = 'attr'
        if not key in json_dict['nodes'][cur_id].keys():
            key = 'attrs'
        assert json_dict['nodes'][cur_id]['op'] == 'tvm_op' and len(assignment[cur_id]) == 3 or \
               json_dict['nodes'][cur_id]['op'] != 'tvm_op'and len(assignment[cur_id]) != 3
        if json_dict['nodes'][cur_id]['op'] == 'tvm_op':
            func_name = json_dict['nodes'][cur_id][key]['func_name']
            kid = assignment[cur_id][2]
            assert -1 not in assignment[cur_id][1]
            
            wait_list = [assignment[id][2] for id in assignment[cur_id][1]]
            assert not len(wait_list) or max(wait_list) < kid

            res['assignment'][kid] = {'func_name': func_name, # func_name for  verification
                                      'stream_id': assignment[cur_id][0],
                                      'wait_list': wait_list,
                                      'emit_order': kid} 
            order['emit_order'].append(kid)
    return res, order

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    parser.add_argument('--extracted_file', type=str, default='', help='tvm json file path')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    extracted_file = args['extracted_file']
    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    res, order = assign_stream(json_dict, wavefront_assign, extracted_file)
    res_json = json.dumps(res, indent=2)
    order_json = json.dumps(order, indent=2)

    res_path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
    order_path = os.path.dirname(os.path.abspath(__file__)) + '/emit_order.json'
    #path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    open(res_path, 'w').write(res_json)
    open(order_path, 'w').write(order_json)
