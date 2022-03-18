import method3

def method5_assign(graph):
    node_finish_time = {}
    stream_finish_time = [0] * 6

    def finish_time_after_assign_node_to_stream(id, sid):
        nonlocal graph, node_finish_time, stream_finish_time
        node_dur = graph.get_duration(id)
        new_finish_time = node_dur + stream_finish_time[sid]
        for input_id in graph.get_inputs(id):
            new_finish_time = max(new_finish_time, node_finish_time[input_id] + node_dur)
        return new_finish_time

    while not graph.is_empty():
        id = graph.ready_nodes()[0]
        num_stream = len(stream_finish_time)
        
        sid_to_assign = 0
        finish_time = 100000
        for sid in range(num_stream):
            t = finish_time_after_assign_node_to_stream(id, sid)
            if t < finish_time:
                sid_to_assign = sid
                finish_time = t
        node_finish_time[id] = stream_finish_time[sid_to_assign] = finish_time
        graph.emit_node(id, sid_to_assign, graph.get_inputs(id))
