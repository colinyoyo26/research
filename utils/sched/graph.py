import copy
import os
from collections import defaultdict
import json
import tvm
from .assigner import Assigner

class Node:
    def __init__(self):
        self.ref_cnt = -1
        self.outputs = []
        self.inputs = []
        self.func_name = ''
        self.duration = -1
        self.grid_size = -1
        self.threads = -1
        self.is_tvm_op = False
        self.stream_id = -1
        self.wait_list = []
        self.emit_order = -1
        self.is_emitted = False

    def is_ready(self):
        return self.ref_cnt == 0

class Graph:
    def __init__(self, model_path, kernel_info=defaultdict(lambda: defaultdict(lambda: 1))):
        json_dict = json.load(open(model_path + '.json'))
        self.model_path = model_path
        self.executor = None

        self.num_node = len(json_dict['nodes'])
        self.num_tvm_op = 0
        self.emit_cnt = 0
        self.consume_nodes = []
        self.nodes = [Node() for _ in range(self.num_node)]
        self.topo_order = []
        for cur_id in range(self.num_node):
            cur_node = json_dict['nodes'][cur_id]

            # set tvm_op
            if cur_node['op'] == 'tvm_op' and cur_node['attrs']['func_name'] != '__nop':
                self.topo_order.append(cur_id)
                self.num_tvm_op += 1
                self.nodes[cur_id].is_tvm_op = True
                key = 'attr'
                if key not in cur_node.keys():
                    key = 'attrs'
                func_name = cur_node[key]['func_name']
                self.nodes[cur_id].func_name = func_name
                self.nodes[cur_id].duration = kernel_info[func_name]['duration'] / 1e3
                self.nodes[cur_id].grid_size = kernel_info[func_name]['grid_size']
                self.nodes[cur_id].warps_per_block = (kernel_info[func_name]['block_size'] + 31) // 32
                self.nodes[cur_id].registers_per_block = kernel_info[func_name]['registers_per_thread'] * kernel_info[func_name]['block_size']
                self.nodes[cur_id].shr_mem_per_block = kernel_info[func_name]['dyn_mem'] + kernel_info[func_name]['stc_mem']
            # build DAG
            inputs = cur_node['inputs']
            for input_id, _, _ in inputs:
                inputs = [input_id]
                if input_id in json_dict['arg_nodes']:
                    inputs = self.nodes[input_id].inputs
                self.nodes[cur_id].inputs += inputs
                
            self.nodes[cur_id].inputs = list(set(self.nodes[cur_id].inputs))
            self.nodes[cur_id].ref_cnt = len(self.nodes[cur_id].inputs)
            
            if cur_id not in json_dict['arg_nodes']:
                for i in self.nodes[cur_id].inputs:
                    self.nodes[i].outputs.append(cur_id)

        
        # assert
        for id in json_dict['arg_nodes']:
            assert not self.nodes[id].is_tvm_op
        for id in self.topo_order:
            assert self.nodes[id].is_tvm_op
            assert all([self.nodes[i].is_tvm_op for i in self.nodes[id].inputs])

        self.ready_list = set([id for id in self.topo_order if not self.nodes[id].ref_cnt])

    def __getitem__(self, i):
        return self.nodes[i]

    def assign(self, graph):
        self.num_node = graph.num_node
        self.num_tvm_op = graph.num_tvm_op
        self.emit_cnt = graph.emit_cnt
        self.consume_nodes = copy.deepcopy(graph.consume_nodes)
        self.nodes = copy.deepcopy(graph.nodes)
        self.ready_list = copy.deepcopy(graph.ready_list)

    def get_topo(self):
        return copy.deepcopy(self.topo_order)

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
                assert self.nodes[output_id].is_tvm_op
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
            if self.nodes[output_id].ref_cnt == 1:
                assert output_id in self.ready_list
                self.ready_list.remove(output_id)
        
        assert self.nodes[id].is_tvm_op

    def reset(self):
        while self.emit_cnt:
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
    
    def get_executor(self):
        import utils
        json, lib, _ = utils.tvm.util.load(self.model_path)
        return tvm.contrib.graph_executor.create(json, lib, tvm.cuda(0))

    def get_latency(self, repeat=50):
        if not self.executor:
            self.executor = self.get_executor()
            for _ in range(20): # warm up
                self.executor.run()
        assigner = self.get_assigner()
        assigner.save_assignment()
        self.executor.set_schedule(assigner.order_path, assigner.assignment_path)
        bench_res = self.executor.benchmark(tvm.cuda(0), repeat=repeat, end_to_end=True)
        res_time = (bench_res.mean * repeat - bench_res.max - bench_res.min) / (repeat - 2)
        return res_time * 1e3
            
    def is_empty(self):
        assert len(self.consume_nodes) == self.emit_cnt
        if len(self.ready_list) == 0:
            assert self.emit_cnt == self.num_tvm_op
        return len(self.ready_list) == 0

    def get_transitive_closure(self, subset):
        subset = set(subset)
        rev_topo = reversed([k for k in self.get_topo() if k in subset])
        tc = defaultdict(lambda: set())
        for id in rev_topo:
            tc[id].add(id)
            outputs = [i for i in self[id].outputs if i in subset]
            for out in outputs:
                tc[id].update(tc[out])
        return tc

    def long_chain(self, tc, subset):
        subset = set(subset)
        suc = defaultdict(lambda: -1)
        depth = defaultdict(lambda: 0)
        topo = [i for i in self.get_topo() if i in subset]
        for id in reversed(topo):
            depth[id] = 0
            outs = [i for i in tc[id] if i in subset and i != id]
            for o in outs:
                if depth[id] < depth[o] + 1:
                    depth[id] = depth[o] + 1
                    suc[id] = o
        u = v = max(depth.keys(), key=lambda x: depth[x])
        chain = []
        while u != -1:
            chain.append(u)
            u = suc[u]
        assert len(chain) == depth[v] + 1
        return chain

    def get_chains(self):
        chains = []
        tc = self.get_transitive_closure(self.get_topo())
        subset = set(self.get_topo())
        while subset:
            chain = self.long_chain(tc, subset)
            chains.append(chain)
            subset -= set(chain)
        return chains
