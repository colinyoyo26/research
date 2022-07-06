
def default_assign(graph, **kwargs):
    for id in graph.get_topo():
        graph.emit_node(id, 0, [])
    return {}
def bfs_assign(graph, **kwargs):
    s = set()
    while not graph.is_empty():
        fringe_nodes = graph.ready_nodes()
        s.add(len(fringe_nodes))
        for sid, id in enumerate(fringe_nodes):
            graph.emit_node(id, sid, graph.get_inputs(id))
    return {'max_ops': max(s)}
