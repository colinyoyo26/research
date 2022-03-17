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
    def __init__(self, assigner=None, model_name='NASNetMobile', batch_size=1):
        file_dir = os.path.dirname(os.path.abspath(__file__))
        tvm_cache = os.path.join(file_dir, '..', 'benchmark', 'tvm_cache', f'{model_name}_{batch_size}')
        json, lib, _ = utils.tvm.util.load(tvm_cache)
        self.executor = graph_executor.create(json, lib, tvm.cuda(0))
        self.set_assigner(assigner)

    def set_assigner(self, assigner):
        self.assigner = copy.deepcopy(assigner)

    def get_profile_time(self):
        self.assigner.save_assignment()
        self.executor.reset()
        self.executor.run() # warm up

        start_time = time.time()
        self.executor.run()
        return time.time() - start_time

    def reset(self):
        self.assigner.reset()

    def undo(self):
        self.assigner.undo()

    def set_node(self, id, sid, wait_list):
        self.assigner.set_node(id, sid, wait_list)
