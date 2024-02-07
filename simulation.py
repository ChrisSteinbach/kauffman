import random
import numpy as np
import result_text
import kauffman
from result_graph import ResultGraph


# Function to dynamically adjust P values based on network conditions
# The basic idea is that a component is more likely to fail, the fewer
# healthy nodes that remain. I imagine this as there being increased load
# on the remaining nodes.
def adjust_p_values(node, expanded_network, states, base_p_values):
    # Decrease P value if a node has more than a threshold of failing downstream nodes
    threshold = 0.5
    downstream_nodes = expanded_network[node]
    if downstream_nodes:
        failing_downstream = sum(not states[down] for down in downstream_nodes) / len(downstream_nodes)
        if failing_downstream > threshold:
            return max(base_p_values[node] * (1 - failing_downstream), 0)  # Adjust P value based on failure rate
    return base_p_values[node]


def initialise_node_states(healthy_node_states, network, stage):
    states = healthy_node_states.copy()

    # Prepare a list of nodes that can potentially fail, excluding health indicators
    potential_nodes_to_fail = [node for node in network.expanded_network if
                               node not in network.get_health_indicator_nodes()]

    # Introduce failures randomly among the potential nodes
    nodes_to_fail = random.sample(potential_nodes_to_fail, min(len(potential_nodes_to_fail), stage))
    for node in nodes_to_fail:
        states[node] = False

    return states


def evaluate_network_health(states, health_indicator_nodes):
    return sum(states[node] for node in health_indicator_nodes) / len(health_indicator_nodes)


def calculate_average_health_by_type(node_health_stats):
    # Group and calculate average health by node type
    type_health_stats = {}
    for node in node_health_stats:
        node_type = ' '.join(node.split()[:-1])  # Extract node type from instance name
        if node_type not in type_health_stats:
            type_health_stats[node_type] = []
        type_health_stats[node_type].extend(node_health_stats[node])
    average_type_health = {node_type: np.mean(healths) for node_type, healths in type_health_stats.items()}
    return average_type_health


class Simulation:
    def __init__(self, num_stages):
        self.num_stages = num_stages
        self.num_runs_per_stage = 2000
        self.num_steps_per_run = 20
        # Failed node recovers after recovery_period runs
        self.recovery_period = 12
        # Threshold for minimum occurrences to consider as potential attractor
        self.purge_threshold = 10
        # Prune low frequency candidate "attractors" after every prune_interval runs
        self.prune_interval = 1000
        self.initial_p_value = 1.0

    def purge_low_attractor_counts(self, attractor_counts):
        return {attractor: count for attractor, count in attractor_counts.items() if count >= self.purge_threshold}

    def run(self, network, result_graph):
        expanded_network = network.expanded_network

        healthy_node_states = {node: True for node in expanded_network}

        # Identify health indicator nodes based on their labels
        health_indicator_nodes = [node for node in expanded_network if node.startswith("Health")]

        total_on_states = 0
        total_evaluations = 0
        attractor_counts = {}

        for stage in range(self.num_stages):
            # To store individual node health across runs
            node_health_stats = {node: [] for node in expanded_network}

            # Initialize base P values for each node type
            base_p_values = {node: self.initial_p_value for node in expanded_network}

            health_sum = 0

            for run in range(self.num_runs_per_stage):
                states = initialise_node_states(healthy_node_states, network, stage)

                # Track failed periods for each node
                failed_periods = {node: 0 for node in expanded_network}

                # Run the simulation for this stage
                for step in range(self.num_steps_per_run):
                    # Dynamically adjust P values at each step
                    current_p_values = {node: adjust_p_values(node, expanded_network, states, base_p_values)
                                        for node in expanded_network}

                    # Update states based on Boolean functions and adjusted P values
                    new_states = states.copy()
                    for node in expanded_network:
                        if not states[node]:
                            # Node remains failed if already failed
                            continue
                        else:
                            # First, determine state based on Boolean function
                            new_states[node] = network.functions[node](
                                [states[neighbor] for neighbor in expanded_network[node]])

                            # Then, modify state based on current P value (additional layer of logic)
                            if np.random.rand() >= current_p_values[node]:
                                # Override state to False based on P value
                                new_states[node] = False
                    states = new_states

                    # Update the counters for P value calculation
                    total_on_states += sum(states.values())
                    total_evaluations += len(states)

                    # Update failed periods and attempt recovery
                    for node in expanded_network:
                        if states[node] == False:
                            failed_periods[node] += 1
                            if failed_periods[node] >= self.recovery_period:
                                states[node] = True  # Node recovers
                                failed_periods[node] = 0  # Reset failed period

                # Evaluate network health and update individual node health
                health_sum += evaluate_network_health(states, health_indicator_nodes)
                for node in expanded_network:
                    node_health_stats[node].append(states[node])

                # Update attractor counts
                attractor_state = frozenset(states.items())
                attractor_counts[attractor_state] = attractor_counts.get(attractor_state, 0) + 1

                # Prune less frequent attractors periodically
                if (stage * self.num_runs_per_stage + run) % self.prune_interval == 0:
                    attractor_counts = self.purge_low_attractor_counts(attractor_counts)

            # Calculate average health for this stage
            average_health = health_sum / self.num_runs_per_stage
            average_type_health = calculate_average_health_by_type(node_health_stats)

            result_text.print_stage_summary(stage, average_health, average_type_health)
            result_graph.add_subgraph(stage)
            # Add nodes with HTML-style labels including health and instance count
            for node_id, label in network.original_label_map.items():
                # Find the instance count by matching the full label
                instance_count = network.instance_counts.get(label, 1)  # Default to 1 if not found
                health = average_type_health.get(label, 0.5)  # Default health if not found
                result_graph.add_node(node_id, stage, label, health, instance_count)

            # Add edges with prefixed node names
            for edge in network.edges():
                result_graph.add_edge(edge, stage)

        P = total_on_states / total_evaluations if total_evaluations > 0 else 0
        attractor_counts = self.purge_low_attractor_counts(attractor_counts)
        # Sorting attractors by their count in descending order
        sorted_attractors = sorted(attractor_counts.items(), key=lambda item: item[1], reverse=True)
        return P, sorted_attractors


def random_sim_kauffman():
    network = kauffman.KauffmanNetwork("plg_example.dot")
    result_graph = ResultGraph()
    num_stages = 10
    simulation = Simulation(num_stages)

    N = network.get_N()
    K = network.get_average_K()
    MAX_K = network.get_max_K()
    P, attractor_counts = simulation.run(network, result_graph)

    # At the end of the script, print the Kauffman network parameters
    print(f"\nKauffman Network Parameters:")
    print(f"N (Total Nodes): {N}")
    print(f"K (Average Inputs per Node): {K}")
    print(f"K (Max Inputs per Node): {MAX_K}")
    print(f"P (Bias in Boolean Functions): {P}")

    # Reporting
    print("Significant Attractors and their occurrence counts:")
    for attractor_state, count in attractor_counts:
        failed_nodes = [node for node, state in attractor_state if not state]
        failed_nodes_str = ', '.join(failed_nodes)
        print(f"Count: {count}, Failed Nodes: {failed_nodes_str}")

    # Function to create HTML-like label for the info box
    def create_info_box_label(N, K, P):
        return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD>N (Total Nodes): {N}</TD></TR><TR><TD>K (Avg. Inputs per Node): {K:.2f}</TD></TR><TR><TD>P (Bias in Boolean Functions): {P}</TD></TR></TABLE>>'

    # Add an info box node
    info_box_label = create_info_box_label(N, K, P)
    result_graph.master_graph.add_node("info_box", label=info_box_label, shape="note", style="filled",
                                       color="lightgrey")

    # Output the combined master graph to a file
    master_graph_dot = result_graph.master_graph.to_string()

    # Get the DOT representation as a string
    dot_content = result_graph.master_graph.to_string()

    # Dynamically generate the alignment snippet based on the number of stages

    # Create align_X node declarations with style=invis
    align_node_declarations = '\n\t\t'.join([f"align_{i} [style=invis];" for i in range(num_stages)])

    # Create align_X -> align_Y edges with style=invis
    align_edges = ' -> '.join([f"align_{i}" for i in range(num_stages)]) + ' [style=invis];'

    # Complete alignment snippet
    alignment_snippet = f"""
    \tsubgraph align {{
            \tgraph [rankdir=LR];
            \t{align_node_declarations}
            \trank=same {align_edges}
    }}
    """

    # Edges from align_X to invisible_X
    for i in range(num_stages):
        alignment_snippet += f"\n\talign_{i} -> invisible_{i} [style=invis];"

    # Insert the alignment snippet before the last closing brace
    modified_dot_content = master_graph_dot.rsplit("}", 1)[0] + alignment_snippet + "}\n"

    # Writing to the file
    with open("combined_stages.dot", "w") as file:
        file.write(modified_dot_content)

random_sim_kauffman()