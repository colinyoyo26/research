import copy
import json
import os

class Assigner:
    def __init__(self, json_dict):
        self.nodes = json_dict['nodes']
        self.num_node = len(json_dict['nodes'])
        # index: node_id, content: [stream_id, wait_events (list of node id), emit order]
        self.assignment = [[] for _ in range(self.num_node)]
        for i in range(self.num_node):
            if self.nodes[i]['op'] == 'tvm_op':
                self.assignment[i] = [-1, [], -1]

    def set_stream_id(self, id, sid):
        self.assignment[id][0] = sid

    def set_wait_list(self, id, wait_list):
        self.assignment[id][1] = copy.deepcopy(wait_list)

    def set_emit_order(self, id, order):
        self.assignment[id][2] = order

    def is_tvm_op(self, id):
        return self.nodes[i]['op'] == 'tvm_op'

    def save_assignment(self):
        num_tvmop = sum([1 for i in self.nodes if i['op'] == 'tvm_op'])

        res = {"assignment": [{}] * num_tvmop}
        order = {'emit_order': []}
        i = 0
        for cur_id in range(self.num_node):
            #assert inDegree[cur_id] == 0
            key = 'attr'
            if not key in self.nodes[cur_id].keys():
                key = 'attrs'
            assert self.nodes[cur_id]['op'] == 'tvm_op' and len(self.assignment[cur_id]) == 3 or \
                   self.nodes[cur_id]['op'] != 'tvm_op' and len(self.assignment[cur_id]) != 3
            if self.nodes[cur_id]['op'] == 'tvm_op':
                func_name = self.nodes[cur_id][key]['func_name']
                kid = self.assignment[cur_id][2]
                assert -1 not in self.assignment[cur_id][1]
            
                wait_list = [self.assignment[id][2] for id in self.assignment[cur_id][1]]
                assert not len(wait_list) or max(wait_list) < kid

                res['assignment'][kid] = {'func_name': func_name, # func_name for  verification
                                          'stream_id': self.assignment[cur_id][0],
                                          'wait_list': wait_list,
                                          'emit_order': kid} 
                order['emit_order'].append(kid)
                
        res_json = json.dumps(res, indent=2)
        order_json = json.dumps(order, indent=2)

        res_path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
        order_path = os.path.dirname(os.path.abspath(__file__)) + '/emit_order.json'

        open(res_path, 'w').write(res_json)
        open(order_path, 'w').write(order_json)
