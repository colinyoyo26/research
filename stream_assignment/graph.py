class Graph:
    def __init__(self, json_dict, kernel_info):
        num_node = len(json_dict['nodes'])
        self.kernel_info = kernel_info
        self.nodes = json_dict['nodes']
        self.adjList = [[] for _ in range(num_node)]
        self.inDegree = [0] * num_node
        for cur_id in range(num_node):
            inputs = json_dict['nodes'][cur_id]['inputs']
            self.inDegree[cur_id] = len(inputs)
            for input_id, _, _ in inputs:
                self.adjList[input_id].append(cur_id)
        
        self.ready_list = set(json_dict['arg_nodes'])
        for cur_id in json_dict['arg_nodes']:
            self.consume(cur_id)

    def ready_nodes(self):
        return list(self.ready_list)

    def consume(self, id):
        assert id in self.ready_list
        for output_id in self.adjList[id]:
            self.inDegree[output_id] -= 1
            if self.inDegree[output_id] == 0:
                self.ready_list.add(output_id)
        self.ready_list.remove(id)

    def kernel_name(self, id):
        key = 'attr'
        if key not in self.nodes[id].keys():
            key = 'attrs'
        return self.nodes[id][key]['func_name']

    def get_utilization(self, id):
        kernel_name = self.kernel_name(id)
        assert kernel_name in self.kernel_info.keys()
        return int(self.kernel_info[kernel_name][0])

    def get_duration(self, id):
        kernel_name = self.kernel_name(id)
        assert kernel_name in self.kernel_info.keys()
        return int(self.kernel_info[kernel_name][1])


    def is_empty(self):
        return len(self.ready_list) == 0
