import tensorflow as tf
import tvm
from tvm.contrib import graph_executor
import numpy as np
import time
import sys
import os
import copy
import json

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
import utils

class Profiler:
    def __init__(self, graph, model_name='NASNetMobile', batch_size=1):
        file_dir = os.path.dirname(os.path.abspath(__file__))
        tvm_cache = os.path.join(file_dir, '..', 'benchmark', 'tvm_cache', f'{model_name}_{batch_size}')
        json, lib, _ = utils.tvm.util.load(tvm_cache)
        self.executor = graph_executor.create(json, lib, tvm.cuda(0))
        self.executor.run() # warm up
        self.graph = graph
        self.reset()

    def get_profile_time(self):
        self.save_assignment()
        self.executor.reset()

        start_time = time.time()
        self.executor.run()
        return time.time() - start_time

    def reset(self):
        self.res = {'assignment': []}
        self.order = {'emit_order': [-1] * self.graph.num_node}
        self.emit_cnt = 0
    
    def emit_node(self, id, sid, wait_list):
        self.res['assignment'].append({
            'func_name': self.graph[id].func_name,
            'stream_id': sid,
            'wait_list': [self.order['emit_order'][i] for i in wait_list],
            'emit_order': self.emit_cnt}) 
        self.order['emit_order'][id] = self.emit_cnt
        self.emit_cnt += 1
    
    def save_assignment(self):
        res_json = json.dumps(self.res, indent=2)
        order_json = json.dumps(self.order, indent=2)

        res_path = os.path.dirname(os.path.abspath(__file__)) + '/assignment.json'
        order_path = os.path.dirname(os.path.abspath(__file__)) + '/emit_order.json'

        open(res_path, 'w').write(res_json)
        open(order_path, 'w').write(order_json)
