import re

import pygraphviz as pgv
from .network_behaviour import interpret_function


def parse_instance_number(instance_name):
    """
    Given an instance name in the format "NodeName X" (with X an integer),
    return X as an integer. Returns None if parsing fails.
    """
    try:
        return int(instance_name.split()[-1])
    except (IndexError, ValueError):
        return None


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


def get_connection_distribution_ratio(connection_type, target_instances):
    """
    Examine the connection_type string and return:
      - ratio (or modulo value),
      - self_connected (a boolean),
      - modulo_mode (a boolean indicating if the "n%X" mode is used)
    """
    # Check for modulo specifier: "1 to n%X"
    mod_match = re.match(r"1 to n%(\d+)", connection_type)
    if mod_match:
        modulo_value = int(mod_match.group(1))
        # For modulo mode, ratio is not used; we simply signal modulo_mode=True.
        return modulo_value, False, True

    # Otherwise, check for a numeric ratio: "1 to (\d+)"
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
    return ratio, self_connected, False


def modulo_filter_targets(modulo_value, src_num, target_instances):
    # Filter targets: only those with the same modulo remainder.
    filtered_targets = [
        target
        for target in target_instances
        if (
            parse_instance_number(target) is not None
            and parse_instance_number(target) % modulo_value == src_num % modulo_value
        )
    ]
    return filtered_targets


class KauffmanNetwork:
    def __init__(self, dot_file):
        self._network = load_network_from_dot(dot_file)
        self._type_to_label_map = {}
        self._instance_to_label_map = {}
        self._instance_counts = {}
        self._input_types = {}
        self._expanded_network = {}
        self._functions = {}
        self._node_type_conditions = {}
        self._load_network()
        self._expand_network()

        # Calculating total connections (Inputs + Outputs) for each node
        self._node_connections = {node: 0 for node in self._expanded_network}

        # Count Inputs
        for node in self._node_connections:
            for source, targets in self._expanded_network.items():
                if node in targets and source:
                    self._node_connections[node] += 1
        output_expanded_network_to_dot(self._expanded_network)

        for node in self._network.nodes():
            num_instances = int(node.attr["instances"] or 1)
            label = node.name
            for i in range(1, num_instances + 1):
                instance_name = f"{label} {i}"
                self._input_types[instance_name] = label

    def get_node_name_to_type_map(self):
        return self._type_to_label_map.items()

    def get_instance_labels(self):
        return self._instance_to_label_map.values()

    def get_node_label(self, node_type):
        return self._type_to_label_map.get(node_type, node_type)

    def get_node_types(self):
        return sorted(self._type_to_label_map.keys())

    def get_instance_label(self, node_type):
        return self._instance_to_label_map.get(node_type, node_type)

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

    def type_condition(self, inputs, node_type):
        types = (node_type,) * len(inputs)
        return self._node_type_conditions[node_type](inputs, types)


    def _load_network(self):
        for node in self._network.nodes():
            node_type = node.name
            self._type_to_label_map[node_type] = node.attr.get("label", node_type)
            type_condition = interpret_function(node.attr["type_condition"] or "one")
            self._node_type_conditions[node_type] = type_condition

            # Assuming the number of instances is stored in a node attribute 'instances'
            # Default to 1 if 'instances' attribute is not found
            self._instance_counts[node_type] = int(node.attr.get("instances") or 1)

    def _expand_network(self):
        self._expand_nodes()
        self._expand_edges()

    def _expand_nodes(self):
        # Expand connections based on expanded nodes
        for node in self._network.nodes():
            num_instances = int(node.attr["instances"] or 1)
            func = interpret_function(node.attr["func"] or "copy")
            for i in range(1, num_instances + 1):
                instance_name = f"{node.name} {i}"
                self._instance_to_label_map[instance_name] = (
                    f"{node.attr.get("label", node.name)} {i}"
                )
                self._expanded_network[instance_name] = []
                self._functions[instance_name] = func

    def _expand_edges(self):
        # Track the number of connections for each target instance to ensure connections are distributed evenly
        target_connections_count = self.init_target_connection_counts()

        for edge in self._network.edges():
            source_instances = self.get_source_instances(edge)
            target_instances = self.get_target_instances(edge)

            connection_type = edge.attr.get("label") or "1 to n"
            ratio_or_modulo, self_connected, modulo_mode = (
                get_connection_distribution_ratio(connection_type, target_instances)
            )
            self.distribute_connections(
                ratio_or_modulo,
                self_connected,
                source_instances,
                target_connections_count,
                target_instances,
                modulo_mode=modulo_mode,
            )

    def init_target_connection_counts(self):
        target_connections_count = {}
        for target in self._expanded_network.keys():
            target_connections_count[target] = 0
        return target_connections_count

    def get_target_instances(self, edge):
        target_pattern = re.compile(f"^{re.escape(edge[1].name)} \\d+$")
        target_instances = [
            n for n in self._expanded_network if target_pattern.match(n)
        ]
        return target_instances

    def get_source_instances(self, edge):
        source_pattern = re.compile(f"^{re.escape(edge[0].name)} \\d+$")
        source_instances = [
            n for n in self._expanded_network if source_pattern.match(n)
        ]
        return source_instances

    def distribute_connections(
        self,
        ratio,
        self_connected,
        source_instances,
        target_connections_count,
        target_instances,
        modulo_mode=False,
    ):
        for source in source_instances:
            if self_connected:
                self._expanded_network[source].append(source)
                target_connections_count[source] += 1
            else:
                targets = target_instances
                if modulo_mode:
                    modulo_value = ratio
                    src_num = parse_instance_number(source)
                    if src_num is None:
                        continue  # Skip if we can't parse the instance number.
                    targets = modulo_filter_targets(
                        modulo_value, src_num, target_instances
                    )
                self.allocate_edges(targets, source, target_connections_count)

    def allocate_edges(self, targets, source, target_connections_count):
        # Sort target instances by their current number of connections, ascending
        sorted_targets = sorted(targets, key=lambda t: target_connections_count[t])
        for target in sorted_targets:
            self._expanded_network[source].append(target)
            target_connections_count[target] += 1
