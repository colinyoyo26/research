
import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import time
import numpy as np
from collections import defaultdict

def reverse_tc(tc):
    rev_tc = defaultdict(lambda: set())
    for id in tc:
        for o in tc[id]:
            rev_tc[o].add(id)
    return rev_tc

def list_to_bits(l):
    if isinstance(l, list):
        return sum([list_to_bits(i) for i in l])
    return 1 << l

def starting_iterator(state, chains, graph, max_groups, max_ops):
    subset = set([i for i in range(graph.num_node) if (1 << i) & state])
    rev_tc = reverse_tc(graph.get_transitive_closure(subset))

    chains = [[i for i in chain if i in subset] for chain in chains]
    chains = [chain[:min(max_ops, len(chains))] for chain in chains if chain and len(rev_tc[chain[0]]) <= max_ops]

    def yield_valid_stages(chain_indices):
        nonlocal chains, rev_tc, max_ops
        
        divs = [1]
        for ci in chain_indices:
            divs.append(len(chains[ci]) * divs[-1])
        total = divs[-1]
        
        for i in range(total):
            stage = []
            stage_ops = set()
            stage_size = 0
            valid = True
            for j, ci in enumerate(chain_indices):
                chain = chains[ci]
                idx = (i // divs[j]) % len(chain)
                assert idx < len(chain)
                stage.append(sorted(rev_tc[chain[idx]]))
                stage_ops.update(stage[-1])
                stage_size += len(stage[-1])
                if len(stage_ops) != stage_size or len(stage[-1]) > max_ops:
                    valid = False
                    break
            valid = valid and len(stage)
            if valid:
                assert len(stage) == len(chain_indices)
                yield stage

    for mask in list(range(1, 1 << len(chains))):
        chain_indices = [i for i in range(len(chains)) if mask & (1 << i)]
        if len(chain_indices) <= min(max_groups, len(chains)):
            yield from yield_valid_stages(chain_indices)

def ios_internal(graph, state, chains, dp, stage_latency, max_groups=8, max_ops=3, prev_ends=[]):
    if graph.is_empty():
        return 0
    if state in dp.keys():
        return dp[state][2]
    prev_time = graph.get_latency()
    for stage in starting_iterator(state, chains, graph, max_groups, max_ops):
        bits = list_to_bits(stage)
        assert (state & bits) == bits or print(state & bits, bits)
        ends = [g[-1] for g in stage]
        for sid, g in enumerate(stage):
            for id in g:
                graph.emit_node(id, sid, [])
            graph.set_wait_list(g[0], prev_ends)
        
        if bits not in stage_latency.keys():
            stage_latency[bits] = max(graph.get_latency() - prev_time, 0)
        #assert stage_time > 0 or print(stage_time, prev_time)

        time = stage_latency[bits] + ios_internal(graph, state ^ bits, chains, dp, stage_latency, max_groups, max_ops, ends)

        if dp[state][2] > time:
            dp[state] = (copy.deepcopy(stage), bits, time)
        
        for _ in range(bin(bits).count('1')):
            graph.undo()
    
    assert state in dp.keys()
    return dp[state][2]

def ios_assign(graph, **kwargs):
    state = sum([1 << i for i in graph.get_topo()])
    dp = defaultdict(lambda: ([], 0, 1000000))
    stage_latency = defaultdict(lambda: -1)
    chains = graph.get_chains()
    ios_internal(graph, state, chains, dp, stage_latency)
   
    total_time = 0
    prev_ends = []
    while not graph.is_empty():
        stage, bits, time = dp[state]
        
        for sid, g in enumerate(stage):
            for id in g:
                graph.emit_node(id, sid, [])
            graph.set_wait_list(g[0], prev_ends)
        
        state = state ^ bits
        total_time += time
        prev_ends = [g[-1] for g in stage]    
    return {'makespan': total_time}
