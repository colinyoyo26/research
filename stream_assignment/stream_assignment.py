import os
import json
import argparse
from collections import deque
from collections import defaultdict

class StreamAssigner:
    def __init__(self, json_dict):
        self.json_dict = json_dict
        self.arg_nodes = json_dict['arg_nodes']
        self.num_node = len(json_dict['nodes'])
        self.adjList = [[] for _ in range(self.num_node)]
        self.inDegree = [0] * self.num_node
        for cur_id in range(self.num_node):
            inputs = json_dict['nodes'][cur_id]['inputs']
            self.inDegree[cur_id] = len(inputs)
            for input_id, _, _ in inputs:
                self.adjList[input_id].append(cur_id)
        self.assign_stream()

    def get(self):
        return self.res

    def assign_stream(self):
        curLevel = deque(self.arg_nodes)
        assignment = [-1] * self.num_node
        while len(curLevel):
            size = len(curLevel)
            for i in range(size):
                cur_id = curLevel.popleft()
                assignment[cur_id] = i
                for output_id in self.adjList[cur_id]:
                    self.inDegree[output_id] -= 1
                    if self.inDegree[output_id] == 0:
                        curLevel.append(output_id)
        
        self.res = defaultdict(lambda: [])
        for cur_id in range(self.num_node):
            key = 'attr'
            if not key in self.json_dict['nodes'][cur_id].keys():
                key = 'attrs'
            if key in self.json_dict['nodes'][cur_id].keys():
                func_name = self.json_dict['nodes'][cur_id][key]['func_name']
                self.res[func_name].append(assignment[cur_id])
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, help='tvm json file path')
    args = vars(parser.parse_args())

    json_path = args['json_path']
    file_name = json_path.split('/')[-1].split('.')[0] + '_assignment.json'

    f = open(json_path)
    json_dict = json.load(f)
    assigner = StreamAssigner(json_dict)
    res_json = json.dumps(assigner.get(), indent=2)

    path = './stream_assignment/assignment.json'
    #path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    open(path, 'w').write(res_json)
