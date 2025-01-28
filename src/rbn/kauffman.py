import re

import pygraphviz as pgv
from .network_behaviour import interpret_function


def update_node_state(node, states, functions, expanded_network, input_types):
    inputs = [states[neighbour] for neighbour in expanded_network[node]]
    types = [input_types[neighbour] for neighbour in expanded_network[node]]
    return functions[node](inputs, types)


def output_expanded_network_to_dot(expanded_network, output_filename="expanded.dot"):
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("digraph ExpandedNetwork {\n")

        # Write nodes
        for node in expanded_network.keys():
            f.write(f'    "{node}" [label="{node}"];\n')

        # Write edges
        for source, targets in expanded_network.items():
            for target in targets:
                f.write(f'    "{source}" -> "{target}";\n')

        f.write("}\n")


def load_network_from_dot(dot_file):
    if dot_file.endswith(".dot"):
        return pgv.AGraph(dot_file)

    return pgv.AGraph(string=dot_file)


class KauffmanNetwork:
    def __init__(self, dot_file):
        self._network = load_network_from_dot(dot_file)
        self._health_percentage = {}
        self.original_label_map = {}
        self._instance_counts = {}
        self._input_types = {}
        self._expanded_network = {}
        self._functions = {}
        self._load_network()
        self._expand_network()

        # Calculating total connections (Inputs + Outputs) for each non-health node
        self._node_connections = {node: 0 for node in self._expanded_network}

        # Count Inputs
        for node in self._node_connections:
            for source, targets in self._expanded_network.items():
                if node in targets and source:
                    self._node_connections[node] += 1
        output_expanded_network_to_dot(self._expanded_network)

        for node in self._network.nodes():
            num_instances = int(node.attr["instances"])
            label = node.attr["label"]
            for i in range(1, num_instances + 1):
                instance_name = f"{label} {i}"
                self._input_types[instance_name] = label

    def get_node_name_to_type_map(self):
        return self.original_label_map.items()

    def get_node_type_instance_count(self, node_type):
        # Note: questionable whether default should be 1 here
        return self._instance_counts.get(node_type, 1)

    def get_expanded_node_list(self):
        return list(self._expanded_network)

    def nodes(self):
        return self._network.nodes()

    def edges(self):
        return self._network.edges()

    def get_n(self):
        # N - Total Number of Nodes
        return len(self._expanded_network)

    def get_average_k(self):
        n = self.get_n()
        return sum(self._node_connections.values()) / n if n > 0 else 0

    def get_max_k(self):
        max_k = (
            max((value, key) for (key, value) in self._node_connections.items())
            if self._node_connections
            else 0
        )
        # print("Max K:" + str(max_k))
        return max_k[0]

    def update_states(self, states):
        # Update states based on Boolean functions and adjusted P values
        expanded_network = self._expanded_network
        new_states = states.copy()
        for node in expanded_network:
            new_states[node] = update_node_state(
                node, states, self._functions, expanded_network, self._input_types
            )
        return new_states

    def health_percentage(self, node_type):
        return self._health_percentage[node_type]

    def _load_network(self):
        for node in self._network.nodes():
            node_type = node.attr["label"]
            health_perc = float(node.attr.get("health_perc") or 0)
            self._health_percentage[node_type] = health_perc

            # Create a mapping from node names to node types
            self.original_label_map[node.name] = node_type

            # Assuming the number of instances is stored in a node attribute 'instances'
            # Default to 1 if 'instances' attribute is not found
            self._instance_counts[node_type] = int(node.attr.get("instances", 1))

    def _expand_network(self):
        self._expand_nodes()
        self._expand_edges()

    def _expand_nodes(self):
        # Expand connections based on expanded nodes
        for node in self._network.nodes():
            num_instances = int(node.attr["instances"])
            func = interpret_function(node.attr["func"])
            for i in range(1, num_instances + 1):
                instance_name = f"{node.attr['label']} {i}"
                self._expanded_network[instance_name] = []
                self._functions[instance_name] = func

    def _expand_edges(self):
        # Track the number of connections for each target instance
        target_connections_count = {}

        for target in self._expanded_network.keys():
            target_connections_count[target] = 0

        for edge in self._network.edges():
            connection_type = edge.attr.get("label") or "1 to n"

            # Compile regex patterns for source and target node matching
            source_pattern = re.compile(f"^{re.escape(edge[0].attr['label'])} \\d+$")
            target_pattern = re.compile(f"^{re.escape(edge[1].attr['label'])} \\d+$")

            source_instances = [
                n for n in self._expanded_network if source_pattern.match(n)
            ]
            target_instances = [
                n for n in self._expanded_network if target_pattern.match(n)
            ]

            # Attempt to extract a specific ratio from the label, defaulting to the length of target_instances
            match = re.match(r"1 to (\d+)", connection_type)
            self_connected = False
            if match:
                ratio = int(match.group(1))
            elif connection_type == "1 to self":
                ratio = 1
                self_connected = True
            else:
                ratio = len(
                    target_instances
                )  # Default ratio to the total number of target instances

            # Distribute connections to target instances with the fewest connections
            for source in source_instances:
                if self_connected:
                    self._expanded_network[source].append(source)
                    target_connections_count[source] += 1
                else:
                    # Sort target instances by their current number of connections, ascending
                    sorted_targets = sorted(
                        target_instances, key=lambda t: target_connections_count[t]
                    )
                    # Assign connections to the targets with the fewest connections
                    for target in sorted_targets[:ratio]:
                        self._expanded_network[source].append(target)
                        target_connections_count[target] += 1  # Update the count
