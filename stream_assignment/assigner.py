import json
import os

class Assigner:
    def __init__(self, graph):
        self.graph = graph
        self.reset()

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
        res_json = json.dumps(self.res, indent=2)
        order_json = json.dumps(self.order, indent=2)

        res_path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
        order_path = os.path.dirname(os.path.abspath(__file__)) + '/emit_order.json'

        open(res_path, 'w').write(res_json)
        open(order_path, 'w').write(order_json)
