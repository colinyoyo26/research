import method3

def method5_assign(graph):
    stream_finish_time = [0] * 6

    def node_earliest_start_time(id):
        nonlocal graph
        inputs = graph.get_inputs(id)
        if not inputs:
            return 0
        return max([graph[i].finish_time for i in inputs])

    while not graph.is_empty():
        id = graph.ready_nodes()[0]
        num_stream = len(stream_finish_time)
        st = node_earliest_start_time(id)
        
        sid = min(enumerate(stream_finish_time), 
            key=lambda x : max(x[1], st))[0]
        finish_time = max(st, stream_finish_time[sid]) \
            + graph.get_duration(id)
        graph[id].finish_time = stream_finish_time[sid] = finish_time 
        graph.emit_node(id, sid, graph.get_inputs(id))
