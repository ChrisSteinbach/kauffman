import pygraphviz as pgv


def record_state_as_graph(attractor_id, state_id, state, network, result_graph):
    node_to_state = dict(state)
    # Add nodes with HTML-style labels including health and instance count
    for node_id, label in network.get_node_name_to_type_map():
        color = "green"
        if not node_to_state[label]:
            color = "red"

        result_graph.add_node(
            f"{attractor_id}_{state_id}_{node_id}",
            style="filled",
            label=label,
            color=color,
        )
    # Add edges with prefixed node names
    for edge in network.edges():
        prefixed_source_id = f"{attractor_id}_{state_id}_{edge[0]}"
        prefixed_target_id = f"{attractor_id}_{state_id}_{edge[1]}"
        result_graph.add_edge(prefixed_source_id, prefixed_target_id)


class AttractorGraph:
    def __init__(self, network, total_runs):
        self._network = network
        self._master_graph = pgv.AGraph(directed=True)
        self._master_graph.graph_attr["rankdir"] = "LR"
        self._attractor_id = 0
        self._total_runs = total_runs

    def add_attractor(self, attractor, count):
        subgraph_label = f"Attractor encountered {count} times. Attractor dominance {round((count / self._total_runs) * 100, 2)}%"
        subgraph_name = f"cluster_{self._attractor_id}"
        attractor_subgraph = self._master_graph.add_subgraph(
            name=subgraph_name,
            label=subgraph_label,
            style="filled",
            fillcolor="lightgrey",
        )
        states = list(attractor)  # Convert tuple to list for indexing
        for i, state in enumerate(states):
            state_id = i
            state_graph_label = f"State {state_id}"
            state_graph_name = f"cluster_{self._attractor_id}_state_{state_id}"
            state_name = f"attractor_{self._attractor_id}_state_{state_id}"

            state_subgraph = attractor_subgraph.add_subgraph(
                name=state_graph_name,
                label=state_graph_label,
                style="filled",
                fillcolor="lightblue",
            )
            if len(states) > 1:
                state_subgraph.add_node(state_name, shape="none", label="", margin="0")

            record_state_as_graph(
                self._attractor_id, state_id, state, self._network, state_subgraph
            )
        if len(states) > 1:
            for i in range(0, len(states) - 1):
                attractor_subgraph.add_edge(
                    f"attractor_{self._attractor_id}_state_{i}",
                    f"attractor_{self._attractor_id}_state_{i + 1}",
                )
            attractor_subgraph.add_edge(
                f"attractor_{self._attractor_id}_state_{len(states) - 1}",
                f"attractor_{self._attractor_id}_state_0",
            )
        self._attractor_id += 1

    def write(self, filename):
        self._master_graph.layout(prog="dot")
        self._master_graph.write(filename)
