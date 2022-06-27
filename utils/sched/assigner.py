import json
import os
import copy

class Assigner:
    def __init__(self, graph):
        self.graph = graph
        self.reset()
        self.assignment_path = graph.model_path + '_assignment.json'
        self.order_path = graph.model_path + '_emit_order.json'

    def reset(self):
        self.res = {'assignment': []}
        self.order = {'emit_order': [-1] * self.graph.num_node}
        self.emit_nodes = []
        self.emit_cnt = 0

    def set_node(self, id, sid, wait_list):
        self.res['assignment'].append({
            'func_name': self.graph[id].func_name,
            'stream_id': sid,
            'wait_list': [self.order['emit_order'][i] for i in wait_list],
            'emit_order': self.emit_cnt}) 
        self.order['emit_order'][id] = self.emit_cnt
        self.emit_nodes.append(id)
        self.emit_cnt += 1
    
    def undo(self):
        id = self.emit_nodes.pop()
        self.res['assignment'].pop()
        self.order['emit_order'][id] = -1
        self.emit_cnt -= 1

    def save_assignment(self):
        self.optimize()
        assignment_json = json.dumps(self.res, indent=2)
        order_json = json.dumps(self.order, indent=2)

        open(self.assignment_path, 'w').write(assignment_json)
        open(self.order_path, 'w').write(order_json)

    def optimize(self):
        for node_info in self.res['assignment']:
            last_emit_nodes = {}
            wait_list = sorted(node_info['wait_list'])
            for wait_emit_order in wait_list:
                sid = self.res['assignment'][wait_emit_order]['stream_id']
                if sid != node_info['stream_id']:
                    last_emit_nodes[sid] = wait_emit_order
            node_info['wait_list'] = [last_emit_nodes[sid] for sid in last_emit_nodes]
