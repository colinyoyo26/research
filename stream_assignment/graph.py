import copy
import os
import json

class Node:
    def __init__(self):
        self.ref_cnt = -1
        self.neighbors = []
        self.func_name = ''
        self.utilization = -1
        self.duration = -1
        self.is_tvm_op = False
        self.stream_id = -1
        self.wait_list = []
        self.emit_order = -1

    def is_ready(self):
        return self.ref_cnt == 0
    
class Graph:
    def __init__(self, json_dict, kernel_info):
        self.num_node = len(json_dict['nodes'])
        self.num_tvm_op = 0
        self.nodes = [Node() for _ in range(self.num_node)]
        for cur_id in range(self.num_node):
            cur_node = json_dict['nodes'][cur_id]
            
            # set tvm_op
            if cur_node['op'] == 'tvm_op':
                self.num_tvm_op += 1
                self.nodes[cur_id].is_tvm_op = True
                key = 'attr'
                if key not in cur_node.keys():
                    key = 'attrs'
                func_name = cur_node[key]['func_name']
                self.nodes[cur_id].func_name = func_name
                self.nodes[cur_id].utilization = kernel_info[func_name][0]
                self.nodes[cur_id].duration = kernel_info[func_name][1]
            
            # build DAG
            inputs = cur_node['inputs']
            self.nodes[cur_id].ref_cnt = len(inputs)
            for input_id, _, _ in inputs:
                self.nodes[input_id].neighbors.append(cur_id)
        
        self.ready_list = set(json_dict['arg_nodes'])
        for cur_id in json_dict['arg_nodes']:
            self.consume(cur_id)

    def ready_nodes(self):
        return list(self.ready_list)

    def consume(self, id):
        assert id in self.ready_list
        for output_id in self.nodes[id].neighbors:
            self.nodes[output_id].ref_cnt -= 1
            if self.nodes[output_id].is_ready():
                self.ready_list.add(output_id)
        self.ready_list.remove(id)

    def kernel_name(self, id):
        return self.nodes[id].func_name

    def get_utilization(self, id):
        return self.nodes[id].utilization

    def get_duration(self, id):
        return self.nodes[id].duration
    
    def set_stream_id(self, id, sid):
        self.nodes[id].stream_id = sid

    def set_wait_list(self, id, wait_list):
        self.nodes[id].wait_list = [self.nodes[i].emit_order for i in wait_list]

    def set_emit_order(self, id, order):
        self.nodes[id].emit_order = order
    
    def save_assignment(self):
        res = {"assignment": [{}] * self.num_tvm_op}
        order = {'emit_order': []}
        i = 0
        for cur_id in range(self.num_node):
            cur_node = self.nodes[cur_id]
            if cur_node.is_tvm_op:
                assert not len(cur_node.wait_list) or max(cur_node.wait_list) <  cur_node.emit_order
                assert -1 not in cur_node.wait_list
                res['assignment'][cur_node.emit_order] = {
                    'func_name': cur_node.func_name, # func_name for verification
                    'stream_id': cur_node.stream_id,
                    'wait_list': cur_node.wait_list,
                    'emit_order': cur_node.emit_order} 
                order['emit_order'].append(cur_node.emit_order)
                
        res_json = json.dumps(res, indent=2)
        order_json = json.dumps(order, indent=2)

        res_path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
        order_path = os.path.dirname(os.path.abspath(__file__)) + '/emit_order.json'

        open(res_path, 'w').write(res_json)
        open(order_path, 'w').write(order_json)

    def is_empty(self):
        return len(self.ready_list) == 0
