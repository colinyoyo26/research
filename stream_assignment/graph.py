import copy
import os
import json
from assigner import Assigner

class Node:
    def __init__(self):
        self.ref_cnt = -1
        self.outputs = []
        self.inputs = []
        self.func_name = ''
        self.utilization = -1
        self.duration = -1
        self.is_tvm_op = False
        self.stream_id = -1
        self.wait_list = []
        self.emit_order = -1
        self.is_emitted = False

    def is_ready(self):
        return self.ref_cnt == 0
    
class Graph:
    def __init__(self, json_dict, kernel_info):
        self.num_node = len(json_dict['nodes'])
        self.num_tvm_op = 0
        self.emit_cnt = 0
        self.consume_nodes = []
        self.nodes = [Node() for _ in range(self.num_node)]

        for cur_id in range(self.num_node):
            cur_node = json_dict['nodes'][cur_id]
            
            # set tvm_op
            if cur_node['op'] == 'tvm_op' and cur_node['attrs']['func_name'] != '__nop':
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
                if input_id not in json_dict['arg_nodes']:
                    self.nodes[cur_id].inputs.append(input_id)
                self.nodes[input_id].outputs.append(cur_id)
        
        for id in json_dict['arg_nodes']:
            assert not self.nodes[id].is_tvm_op

        self.ready_list = set(json_dict['arg_nodes'])
        for cur_id in json_dict['arg_nodes']:
            self.consume(cur_id)

    def __getitem__(self, i):
        return self.nodes[i]

    def assign(self, graph):
        self.num_node = graph.num_node
        self.num_tvm_op = graph.num_tvm_op
        self.emit_cnt = graph.emit_cnt
        self.consume_nodes = copy.deepcopy(graph.consume_nodes)
        self.nodes = copy.deepcopy(graph.nodes)
        self.ready_list = copy.deepcopy(graph.ready_list)

    def ready_nodes(self):
        return list(self.ready_list)

    def is_emitted(self, id):
        return self.nodes[id].is_emitted

    def kernel_name(self, id):
        return self.nodes[id].func_name

    def get_num_nodes(self):
        return self.num_node

    def get_inputs(self, id):
        return copy.deepcopy(self.nodes[id].inputs)

    def get_outputs(self, id):
        return copy.deepcopy(self.nodes[id].outputs)

    def get_utilization(self, id):
        return self.nodes[id].utilization

    def get_duration(self, id):
        return self.nodes[id].duration
    
    def set_stream_id(self, id, sid):
        self.nodes[id].stream_id = sid

    def set_wait_list(self, id, wait_list):
        self.nodes[id].wait_list = copy.deepcopy(wait_list)

    def set_emit_order(self, id, order):
        self.nodes[id].emit_order = order
    
    def consume(self, id):
        assert id in self.ready_list or print(id)
        for output_id in self.nodes[id].outputs:
            self.nodes[output_id].ref_cnt -= 1
            if self.nodes[output_id].is_ready():
                self.ready_list.add(output_id)
                if not self.nodes[output_id].is_tvm_op:
                    self.consume(output_id)
        self.ready_list.remove(id)
        self.consume_nodes.append(id)

    def undo(self):
        id = self.consume_nodes.pop()
        
        if self.nodes[id].is_tvm_op:
            assert self.nodes[id].is_emitted
            self.emit_cnt -= 1
            self.ready_list.add(id)
            self.set_stream_id(id, -1)
            self.set_wait_list(id, [])
            self.set_emit_order(id, -1)
            self.nodes[id].is_emitted = False
        
        for output_id in self.nodes[id].outputs:
            self.nodes[output_id].ref_cnt += 1
            if self.nodes[output_id] == 1:
                assert output_id in ready_list or not self.nodes[output_id].is_tvm_op
                self.ready_list.remove(output_id)
        
        if not self.nodes[id].is_tvm_op:
            assert self.emit_nodes[-1] in self.nodes[id].inputs
            self.undo()

    def reset(self):
        while self.consume_nodes:
            self.undo()

    def emit_node(self, id, sid, wait_list):
        self.set_stream_id(id, sid)
        self.set_wait_list(id, wait_list)
        self.set_emit_order(id, self.emit_cnt)
        self.emit_cnt += 1
        self.consume(id)
        self.nodes[id].is_emitted = True

    def get_assigner(self):
        assigner = Assigner(self)
        for id in self.consume_nodes:
            if self[id].is_tvm_op:
                assigner.set_node(id, self[id].stream_id, self[id].wait_list)
        return assigner

    def save_assignment(self):
        assigner = self.get_assigner()
        assigner.save_assignment()
            
    def is_empty(self):
        return len(self.ready_list) == 0
