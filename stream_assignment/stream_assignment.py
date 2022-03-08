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
def wavefront_assign(json_dict, adjList, inDegree, assigner, extracted_file=''):
    arg_nodes = json_dict['arg_nodes']
    num_node = len(json_dict['nodes'])
    curLevel = copy.deepcopy(arg_nodes)

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
                    assigner.set_stream_id(output_id, len(nextLevel))
                    assigner.set_emit_order(output_id, emit_order)
                    assigner.set_wait_list(output_id, wait_list)
                    emit_order += 1
                    nextLevel.append(output_id)
        curLevel = nextLevel
        wait_list = curLevel

def default_assign(json_dict, adjList, inDegree, assigner, extracted_file):
    num_node = len(json_dict['nodes'])
    cnt = 0
    for i in range(num_node):
        if json_dict['nodes'][i]['op'] == 'tvm_op':
            assigner.set_stream_id(i, 0)
            assigner.set_wait_list(i, [])
            assigner.set_emit_order(i, cnt)
            cnt += 1

# profiled based
def test_assign(json_dict, adjList, inDegree, assigner, extracted_file):
    kernel_info = nvlog.info.get_kernel_info(extracted_file)
    print(kernel_info)

def assign_stream(json_dict, assign_func, extracted_file):
    num_node = len(json_dict['nodes'])
    adjList, inDegree = buildGraph(json_dict)

    assigner = Assigner(json_dict)
    assign_func(json_dict, adjList, inDegree, assigner, extracted_file)
    assigner.save_assignment()

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
    assign_stream(json_dict, default_assign, extracted_file)
