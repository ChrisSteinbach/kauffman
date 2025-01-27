import os
import random
import re
import sys

import numpy as np
import pygraphviz as pgv
from rbn import kauffman
from rbn.kauffman import update_states
from rbn.result_graph import ResultGraph, AbstractResultGraph
from rbn.result_text import ResultText, AbstractResultText


def normalize_frozenset(frozen_set_instance):
    """Convert frozenset into a sorted tuple for consistent ordering."""
    return tuple(sorted(frozen_set_instance))


def normalize_tuple(cyclic_tuple):
    """Normalize a tuple of frozensets as a cycle."""
    # First, normalize each frozenset to ensure consistent order
    normalized_parts = tuple(
        normalize_frozenset(frozen_set_instance) for frozen_set_instance in cyclic_tuple
    )

    # Generate all rotations of the tuple
    rotations = [
        normalized_parts[i:] + normalized_parts[:i]
        for i in range(len(normalized_parts))
    ]

    # Return the lexicographically smallest rotation
    return min(rotations)


def initialise_node_states(healthy_node_states, network, stage):
    states = healthy_node_states.copy()

    # Prepare a list of nodes that can potentially fail, excluding health indicators
    potential_nodes_to_fail = list(network.expanded_network)

    # Introduce failures randomly among the potential nodes
    nodes_to_fail = random.sample(
        potential_nodes_to_fail, min(len(potential_nodes_to_fail), stage)
    )
    for node in nodes_to_fail:
        states[node] = False

    return states


def calculate_average_health_by_type(node_health_stats):
    # Group and calculate average health by node type
    type_health_stats = {}
    for node in node_health_stats:
        node_type = " ".join(node.split()[:-1])  # Extract node type from instance name
        if node_type not in type_health_stats:
            type_health_stats[node_type] = []
        type_health_stats[node_type].extend(node_health_stats[node])
    average_type_health = {
        node_type: np.mean(healths) for node_type, healths in type_health_stats.items()
    }
    return average_type_health


def evaluate_and_update_health(expanded_network, node_health_stats, states):
    # Update individual node health
    for node in expanded_network:
        node_health_stats[node].append(states[node])


def record_result_as_subgraph(average_type_health, network, result_graph, stage):
    result_graph.add_subgraph(stage)
    # Add nodes with HTML-style labels including health and instance count
    for node_id, label in network.original_label_map.items():
        # Find the instance count by matching the full label
        instance_count = network.instance_counts.get(
            label, 1
        )  # Default to 1 if not found
        health = average_type_health.get(label, 0.5)  # Default health if not found
        result_graph.add_node(node_id, stage, label, health, instance_count)
    # Add edges with prefixed node names
    for edge in network.edges():
        result_graph.add_edge(edge, stage)


def remove_trailing_integer(input_string):
    pattern = r".*\s\d+$"

    # Check if the input string matches the pattern.
    # If it does, remove the last space and the digits following it.
    if re.match(pattern, input_string):
        # The regex here matches a space (\s) followed by one or more digits (\d+) at the end of the string ($)
        # and replaces it with an empty string, effectively removing it.
        return re.sub(r"\s\d+$", "", input_string)

    # If the input string does not match the pattern, return it unchanged
    return input_string


def normalize_attractor(attractor, network):
    # Dict to hold counts of True/False states per node type
    state_counts = {}
    for node_state in attractor:
        node_type, state = remove_trailing_integer(node_state[0]), node_state[1]
        if node_type not in state_counts:
            state_counts[node_type] = {"True": 0, "False": 0}
        state_counts[node_type][str(state)] += 1

    # Generate a normalized attractor based on state counts as a percentage healthy
    return frozenset(
        (
            node_type,
            (
                state_counts[node_type]["True"]
                / (state_counts[node_type]["True"] + state_counts[node_type]["False"])
            )
            > network.health_percentage[node_type],
        )
        for node_type in state_counts
    )


def update_attractor_counts(attractor_counts, states):
    # Update attractor counts
    attractor_state = normalize_tuple(tuple(states))
    attractor_counts[attractor_state] = attractor_counts.get(attractor_state, 0) + 1
    return attractor_counts


class Simulation:
    def __init__(self, num_stages):
        self.num_stages = num_stages
        self.num_runs_per_stage = 2000
        self.num_steps_per_run = 40

    def run(
        self,
        network,
        result_graph=AbstractResultGraph(),
        result_text=AbstractResultText(),
    ):
        expanded_network = network.expanded_network

        healthy_node_states = {node: True for node in expanded_network}

        total_on_states = 0
        total_evaluations = 0
        attractor_counts = {}
        runs_with_attractor = 0
        runs_no_attractor = 0

        for stage in range(self.num_stages):
            # To store individual node health across runs
            node_health_stats = {node: [] for node in expanded_network}

            for _ in range(self.num_runs_per_stage):
                (
                    attractor_counts,
                    total_evaluations,
                    total_on_states,
                    attractor_found,
                ) = self.run_single_simulation(
                    attractor_counts,
                    expanded_network,
                    healthy_node_states,
                    network,
                    node_health_stats,
                    stage,
                    total_evaluations,
                    total_on_states,
                )
                if attractor_found:
                    runs_with_attractor = runs_with_attractor + 1
                else:
                    runs_no_attractor = runs_no_attractor + 1

            # Calculate average health for this stage
            average_type_health = calculate_average_health_by_type(node_health_stats)

            result_text.print_stage_summary(stage, average_type_health)
            record_result_as_subgraph(average_type_health, network, result_graph, stage)

        p = total_on_states / total_evaluations if total_evaluations > 0 else 0
        n = network.get_n()
        k = network.get_average_k()
        max_k = network.get_max_k()

        result_text.print_attractor_summary(
            attractor_counts, runs_with_attractor, runs_no_attractor
        )
        result_text.print_kauffman_parameters(k, max_k, n, p)

        if len(attractor_counts) < 20:
            print("Creating attractor graph")
            create_attractor_graph(attractor_counts, network)

        result_graph.add_info_box(k, max_k, n, p)
        return p, len(attractor_counts)

    def run_single_simulation(
        self,
        attractor_counts,
        expanded_network,
        healthy_node_states,
        network,
        node_health_stats,
        stage,
        total_evaluations,
        total_on_states,
    ):
        state_history = []
        attractor_found = False
        attractor_sequence = []
        states = initialise_node_states(healthy_node_states, network, stage)
        # Run the simulation for this stage
        for step in range(self.num_steps_per_run):
            states = update_states(expanded_network, network, states)

            # Update the counters for P value calculation
            total_on_states += sum(states.values())
            total_evaluations += len(states)

            current_state = normalize_attractor(frozenset(states.items()), network)
            if current_state in state_history:
                attractor_index = state_history.index(current_state)
                attractor_sequence = state_history[attractor_index:]
                attractor_found = True
                break
            else:
                state_history.append(current_state)
        evaluate_and_update_health(expanded_network, node_health_stats, states)
        if attractor_found:
            # Process the found attractor sequence
            attractor_counts = update_attractor_counts(
                attractor_counts, attractor_sequence
            )
        return attractor_counts, total_evaluations, total_on_states, attractor_found


def record_state_as_graph(attractor_id, state_id, state, network, result_graph):
    node_to_state = {key: value for key, value in state}
    # Add nodes with HTML-style labels including health and instance count
    for node_id, label in network.original_label_map.items():
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


def create_attractor_graph(attractors, network):
    g = pgv.AGraph(directed=True)
    g.graph_attr["rankdir"] = "LR"
    attractor_id = 0
    total = sum(attractors.values())

    for attractor, count in attractors.items():
        subgraph_label = f"Attractor encountered {count} times. Attractor dominance {round((count / total)*100, 2)}%"
        subgraph_name = f"cluster_{attractor_id}"
        sub_g = g.add_subgraph(
            name=subgraph_name,
            label=subgraph_label,
            style="filled",
            fillcolor="lightgrey",
        )
        states = list(attractor)  # Convert tuple to list for indexing
        for i, state in enumerate(states):
            state_id = i
            state_graph_label = f"State {state_id}"
            state_graph_name = f"cluster_{attractor_id}_state_{state_id}"
            state_name = f"attractor_{attractor_id}_state_{state_id}"

            sub_a = sub_g.add_subgraph(
                name=state_graph_name,
                label=state_graph_label,
                style="filled",
                fillcolor="lightblue",
            )
            if len(states) > 1:
                sub_a.add_node(state_name, shape="none", label="", margin="0")

            record_state_as_graph(attractor_id, state_id, state, network, sub_a)
        if len(states) > 1:
            for i in range(0, len(states) - 1):
                sub_g.add_edge(
                    f"attractor_{attractor_id}_state_{i}",
                    f"attractor_{attractor_id}_state_{i + 1}",
                )
            sub_g.add_edge(
                f"attractor_{attractor_id}_state_{len(states)-1}",
                f"attractor_{attractor_id}_state_0",
            )
        attractor_id += 1
    g.layout(prog="dot")
    g.write("attractors_graph.dot")


def random_sim_kauffman(output_dot_file):
    network = kauffman.KauffmanNetwork(output_dot_file)
    result_graph = ResultGraph()
    result_text = ResultText()
    num_stages = 16
    simulation = Simulation(num_stages)
    simulation.run(network, result_graph, result_text)
    result_graph.write(num_stages, "combined_stages.dot")


if __name__ == "__main__":

    # Check if exactly one argument is passed (excluding the script name)
    if len(sys.argv) != 2:
        print("Usage: python simulation.py <file.dot>")
        sys.exit(1)

    # Get the filename from the command-line arguments
    dot_file = sys.argv[1]

    # Check if the file has a .dot extension
    if not dot_file.endswith(".dot"):
        print(f"Error: The file '{dot_file}' does not have a .dot extension.")
        sys.exit(1)

    # Check if the file exists
    if not os.path.exists(dot_file):
        print(f"Error: The file '{dot_file}' does not exist.")
        sys.exit(1)

    # File exists and has .dot extension
    print(f"File '{dot_file}' is valid and ready for use.")

    random_sim_kauffman(dot_file)
