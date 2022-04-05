import tensorflow as tf
import tvm
from tvm.contrib import graph_executor
import numpy as np
import time
import sys
import os
import copy
import json
from assigner import Assigner

ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(ROOT_PATH)
import utils

class Profiler:
    def __init__(self, model_path, assigner=None):
        file_dir = os.path.dirname(os.path.abspath(__file__))
        json, lib, _ = utils.tvm.util.load(model_path)
        self.executor = graph_executor.create(json, lib, tvm.cuda(0))
        self.set_assigner(assigner)

    def set_assigner(self, assigner):
        self.assigner = copy.deepcopy(assigner)

    def get_profile_time(self, warm_runs=10):
        self.assigner.save_assignment()
        self.executor.set_schedule('../stream_assignment/emit_order.json', '../stream_assignment/assignment.json')
        for _ in range(warm_runs):
            self.executor.run() # warm up
        repeat = 20
        bench_res = self.executor.benchmark(tvm.cuda(0), repeat=repeat, end_to_end=True)
        res_time = (bench_res.mean * repeat - bench_res.max - bench_res.min) / (repeat - 2)
        return res_time

    def reset(self):
        self.assigner.reset()

    def undo(self):
        self.assigner.undo()

    def set_node(self, id, sid, wait_list):
        self.assigner.set_node(id, sid, wait_list)
