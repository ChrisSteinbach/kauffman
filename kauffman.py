import pygraphviz as pgv
import re
from network_behaviour import interpret_function


class KauffmanNetwork:
    def __init__(self, dot_file):
        if dot_file.endswith(".dot"):
            self.network = pgv.AGraph(dot_file)
        else:
            self.network = pgv.AGraph(string=dot_file)

        self.expanded_network = {}
        self.functions = {}
        self.original_label_map = {}
        self.instance_counts = {}
        self._load_network()
        self._expand_network()
        #print(self.expanded_network)
        self.health_indicator_nodes = [node for node in self.expanded_network if node.startswith("Health")]

        # Calculating total connections (Inputs + Outputs) for each non-health node
        self.node_connections = {node: 0 for node in self.expanded_network if node not in self.health_indicator_nodes}

        # Count Outputs
        for node, neighbors in self.expanded_network.items():
            if node not in self.health_indicator_nodes:
                self.node_connections[node] += len([n for n in neighbors if n not in self.health_indicator_nodes])

        # Count Inputs
        for node in self.node_connections:
            for source, targets in self.expanded_network.items():
                if node in targets and source not in self.health_indicator_nodes:
                    self.node_connections[node] += 1

    def nodes(self):
        return self.network.nodes()

    def edges(self):
        return self.network.edges()

    def get_health_indicator_nodes(self):
        return self.health_indicator_nodes

    def get_N(self):
        # N - Total Number of Nodes
        return len(self.expanded_network)

    def get_average_K(self):
        N = self.get_N()
        return sum(self.node_connections.values()) / N if N > 0 else 0

    def get_max_K(self):
        max_k = max((value, key) for (key, value) in self.node_connections.items()) if self.node_connections else 0
        print("Max K:" + str(max_k))
        return max_k[0]

    def _load_network(self):
        for node in self.network.nodes():
            node_type = node.attr['label']

            # Create a mapping from node names to node types
            self.original_label_map[node.name] = node_type

            # Assuming the number of instances is stored in a node attribute 'instances'
            # Default to 1 if 'instances' attribute is not found
            self.instance_counts[node_type] = int(node.attr.get('instances', 1))

    def _expand_network(self):
        self._expand_nodes()
        self._expand_edges()

    def _expand_nodes(self):
        # Expand connections based on expanded nodes
        for node in self.network.nodes():
            num_instances = int(node.attr['instances'])
            func = interpret_function(node.attr['func'])
            for i in range(1, num_instances + 1):
                instance_name = f"{node.attr['label']} {i}"
                self.expanded_network[instance_name] = []
                self.functions[instance_name] = func

    def _expand_edges(self):
        for edge in self.network.edges():
            connection_type = edge.attr.get('label') or '1 to n'

            # Compile regex patterns for source and target node matching
            source_pattern = re.compile(f"^{re.escape(edge[0].attr['label'])} \\d+$")
            target_pattern = re.compile(f"^{re.escape(edge[1].attr['label'])} \\d+$")

            source_instances = [n for n in self.expanded_network if source_pattern.match(n)]
            target_instances = [n for n in self.expanded_network if target_pattern.match(n)]

            # Attempt to extract a specific ratio from the label, defaulting to the length of target_instances
            match = re.match(r'1 to (\d+)', connection_type)
            if match:
                ratio = int(match.group(1))
            else:
                ratio = len(target_instances)  # Default ratio to the total number of target instances

            target_instances = target_instances * len(source_instances)

            # Apply "1 to n" logic with the determined ratio
            for i, source in enumerate(source_instances):
                assigned_targets = target_instances[i * ratio: (i + 1) * ratio]
                for target in assigned_targets:
                    self.expanded_network[source].append(target)
