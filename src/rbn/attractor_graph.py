import pygraphviz as pgv

from .incidence_matrix import (
    build_html_table,
    build_incidence_matrix_from_attractor_counts,
)


def create_info_box_label(N, K, MAX_K, P):
    return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD>N (Total Nodes): {N}</TD></TR><TR><TD>K (Avg. Inputs per Node): {K:.2f}</TD></TR><TR><TD>K (Max Inputs per Node): {MAX_K:.2f}</TD></TR><TR><TD>P (Bias in Boolean Functions): {P}</TD></TR></TABLE>>'


class StateGraph:
    def __init__(self, attractor_id, state_id, attractor_subgraph, network):
        self._network = network
        self._attractor_id = attractor_id
        self._state_id = state_id
        state_graph_label = f"State {state_id}"
        state_graph_name = f"cluster_{self._attractor_id}_state_{state_id}"
        self._graph = attractor_subgraph.add_subgraph(
            name=state_graph_name,
            label=state_graph_label,
            style="filled",
            fillcolor="lightblue",
        )

    def record_state_as_graph(self, state, is_cyclic):
        node_to_state = dict(state)
        self.add_nodes(node_to_state)
        self.add_edges()
        if is_cyclic:
            state_name = f"attractor_{self._attractor_id}_state_{self._state_id}"
            self._graph.add_node(state_name, shape="none", label="", margin="0")

    def add_edges(self):
        for edge in self._network.edges():
            prefixed_source_id = f"{self._attractor_id}_{self._state_id}_{edge[0]}"
            prefixed_target_id = f"{self._attractor_id}_{self._state_id}_{edge[1]}"
            self._graph.add_edge(prefixed_source_id, prefixed_target_id)

    def add_nodes(self, node_to_state):
        for node_name, node_label in self._network.get_node_name_to_type_map():
            color = "green"
            if not node_to_state[node_name]:
                color = "red"

            self._graph.add_node(
                f"{self._attractor_id}_{self._state_id}_{node_name}",
                style="filled",
                label=node_label,
                color=color,
            )


class AttractorGraph:
    def __init__(self, network, total_runs):
        self._network = network
        self._master_graph = pgv.AGraph(directed=True)
        self._master_graph.graph_attr["rankdir"] = "LR"
        self._attractor_id = 0
        self._total_runs = total_runs

    def add_attractor(self, attractor, attractor_id, count):
        subgraph_label = f"Attractor #{attractor_id}, {count} stressors encountered. Attractor dominance {round((count / self._total_runs) * 100, 2)}%"
        subgraph_name = f"cluster_{self._attractor_id}"
        attractor_subgraph = self._master_graph.add_subgraph(
            name=subgraph_name,
            label=subgraph_label,
            style="filled",
            fillcolor="lightgrey",
        )
        states = list(attractor)  # Convert tuple to list for indexing
        is_cyclic = len(states) > 1
        for state_id, state in enumerate(states):
            state_graph = StateGraph(
                self._attractor_id, state_id, attractor_subgraph, self._network
            )
            state_graph.record_state_as_graph(state, is_cyclic)
        if is_cyclic:
            self.link_states(attractor_subgraph, states)
        self._attractor_id += 1

    def link_states(self, attractor_subgraph, states):
        for i in range(0, len(states)):
            attractor_subgraph.add_edge(
                f"attractor_{self._attractor_id}_state_{i}",
                f"attractor_{self._attractor_id}_state_{(i + 1) % len(states)}",
            )

    def add_state(self, attractor_subgraph, state_id, state, states):
        is_cyclic = len(states) > 1
        state_graph = StateGraph(
            self._attractor_id, state_id, attractor_subgraph, self._network
        )
        state_graph.record_state_as_graph(state, is_cyclic)

    def add_incidence_matrix(self, attractors):
        incidence_matrix, attractor_ids = build_incidence_matrix_from_attractor_counts(
            attractors, self._network
        )
        incidence_matrix_table = build_html_table(
            incidence_matrix, attractor_ids, self._network
        )
        self._master_graph.add_node(
            "incidence_matrix",
            label=f"<{incidence_matrix_table}>",
            shape="note",
            style="filled",
            color="lightgrey",
        )

    def add_info_box(self, K, MAX_K, N, P):
        # Add an info box node
        info_box_label = create_info_box_label(N, K, MAX_K, P)
        self._master_graph.add_node(
            "info_box",
            label=info_box_label,
            shape="note",
            style="filled",
            color="lightgrey",
        )

    def write(self, filename):
        self._master_graph.layout(prog="dot")
        self._master_graph.write(filename)
