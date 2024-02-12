import random
import numpy as np
import result_text
import kauffman
from result_graph import ResultGraph
from result_text import print_kauffman_parameters, print_attractor_summary


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
    if len(health_indicator_nodes) == 0:
        return 0
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


def evaluate_and_update_health(expanded_network, health_indicator_nodes, health_sum, node_health_stats,
                               states):
    # Evaluate network health and update individual node health
    health_sum += evaluate_network_health(states, health_indicator_nodes)
    for node in expanded_network:
        node_health_stats[node].append(states[node])
    return health_sum


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

            health_sum = 0

            for run in range(self.num_runs_per_stage):
                states = initialise_node_states(healthy_node_states, network, stage)

                # Track failed periods for each node
                failed_periods = {node: 0 for node in expanded_network}

                # Run the simulation for this stage
                for step in range(self.num_steps_per_run):
                    states = self.update_states(expanded_network, network, states)

                    # Update the counters for P value calculation
                    total_on_states += sum(states.values())
                    total_evaluations += len(states)

                    self.update_failed_periods_and_recoveries(expanded_network, failed_periods, states)

                health_sum = evaluate_and_update_health(expanded_network, health_indicator_nodes, health_sum,
                                                        node_health_stats, states)

                attractor_counts = self.update_attractor_counts(attractor_counts, run, stage, states)

            # Calculate average health for this stage
            average_health = health_sum / self.num_runs_per_stage
            average_type_health = calculate_average_health_by_type(node_health_stats)

            result_text.print_stage_summary(stage, average_health, average_type_health)
            self.record_result_as_subgraph(average_type_health, network, result_graph, stage)

        P = total_on_states / total_evaluations if total_evaluations > 0 else 0
        N = network.get_N()
        K = network.get_average_K()
        MAX_K = network.get_max_K()

        print_kauffman_parameters(K, MAX_K, N, P)

        attractor_counts = self.purge_low_attractor_counts(attractor_counts)
        print_attractor_summary(attractor_counts)

        result_graph.add_info_box(K, MAX_K, N, P)

    def record_result_as_subgraph(self, average_type_health, network, result_graph, stage):
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

    def update_states(self, expanded_network, network, states):
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
        states = new_states
        return states

    def update_attractor_counts(self, attractor_counts, run, stage, states):
        # Update attractor counts
        attractor_state = frozenset(states.items())
        attractor_counts[attractor_state] = attractor_counts.get(attractor_state, 0) + 1
        # Prune less frequent attractors periodically
        if (stage * self.num_runs_per_stage + run) % self.prune_interval == 0:
            attractor_counts = self.purge_low_attractor_counts(attractor_counts)
        return attractor_counts

    def update_failed_periods_and_recoveries(self, expanded_network, failed_periods, states):
        # Update failed periods and attempt recovery
        for node in expanded_network:
            if states[node] == False:
                failed_periods[node] += 1
                if failed_periods[node] >= self.recovery_period:
                    states[node] = True  # Node recovers
                    failed_periods[node] = 0  # Reset failed period


def random_sim_kauffman():
    network = kauffman.KauffmanNetwork("plg_example.dot")
    result_graph = ResultGraph()
    num_stages = 8
    simulation = Simulation(num_stages)
    simulation.run(network, result_graph)

    result_graph.write(num_stages, "combined_stages.dot")


random_sim_kauffman()
