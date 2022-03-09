class Node:
    def __init__(self):
        self.ref_cnt = -1
        self.neighbors = []
        self.func_name = ''
        self.utilization = -1
        self.duration = -1
    
    def is_ready(self):
        return self.ref_cnt == 0

class Graph:
    def __init__(self, json_dict, kernel_info):
        num_node = len(json_dict['nodes'])
        self.nodes = [Node() for _ in range(num_node)]
        for cur_id in range(num_node):
            cur_node = json_dict['nodes'][cur_id]
            
            # set tvm_op
            if cur_node['op'] == 'tvm_op':
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

    def is_empty(self):
        return len(self.ready_list) == 0
