def default_assign(graph, **kwargs):
    while not graph.is_empty():
        for id in graph.ready_nodes():
            graph.emit_node(id, 0, [])

def bfs_assign(graph, **kwargs):
    while not graph.is_empty():
        fringe_nodes = graph.ready_nodes()
        for sid, id in enumerate(fringe_nodes):
            graph.emit_node(id, sid, graph.get_inputs(id))
