import copy

def fill_stage(graph, threshold):
    curLevel = graph.ready_nodes()
    utilizations = [int(graph.get_utilization(id)) for id in curLevel]
    if max(utilizations) >= threshold:
        return [curLevel[max(enumerate(utilizations), key=lambda x : x[1])[0]]]

    n = len(curLevel)
    prev_dp = [0] * (threshold + 1)
    record = [[False] * (threshold + 1) for _ in range(n)]
    for i in range(1, n + 1, 1):
        cur_dp = [0] * (threshold + 1)
        # can't have 0 utilization
        w = utilizations[i - 1] = max(utilizations[i - 1], 1)
        for j in range(threshold + 1):
            cur_dp[j] = prev_dp[j]
            if j >= w and w + prev_dp[j - w] > cur_dp[j]:
                cur_dp[j] = w + prev_dp[j - w]
                record[i - 1][j] = True
        prev_dp = cur_dp
    
    assert prev_dp[threshold] > 0 or print(utilizations)
    result = []
    remain = threshold
    for i in range(n - 1, -1, -1):
        if record[i][remain]:
            result.append(curLevel[i])
            remain -= utilizations[i]
    assert threshold - remain == prev_dp[threshold] or print(threshold - remain, prev_dp[threshold])
    return result

def update_stream_ends(graph, id, stream_ends):
    sid = graph[id].stream_id
    assert sid <= len(stream_ends)
    if sid == len(stream_ends):
        stream_ends.append(id)
    assert graph[id].emit_order >= graph[stream_ends[sid]].emit_order
    stream_ends[sid] = id

# profiled based / non stage
def method1_assign(graph, threshold=100, **kwargs):
    while not graph.is_empty():
        node_ids = fill_stage(graph, threshold)    
        for sid, id in enumerate(node_ids):
            graph.emit_node(id, sid, graph.get_inputs(id))
        
# profile based / stage 
def method1_stage_assign(graph, threshold=400, **kwargs):
    stream_ends = []
    while not graph.is_empty():
        next_stream_ends = copy.deepcopy(stream_ends)
        node_ids = fill_stage(graph, threshold) 
        for sid, id in enumerate(node_ids):
            graph.emit_node(id, sid, stream_ends)
            update_stream_ends(graph, id, next_stream_ends)
        stream_ends = next_stream_ends
