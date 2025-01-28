import os
import random
import re
import sys

import numpy as np
from rbn import kauffman
from rbn.attractor_graph import AttractorGraph
from rbn.result_graph import ResultGraph, AbstractResultGraph
from rbn.result_text import ResultText, AbstractResultText
from rbn.attractors import Attractors


def initialise_node_states(healthy_node_states, network, stage):
    states = healthy_node_states.copy()

    # Prepare a list of nodes that can potentially fail, excluding health indicators
    potential_nodes_to_fail = network.get_expanded_node_list()

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


def evaluate_and_update_health(network, node_health_stats, states):
    # Update individual node health
    for node in network.get_expanded_node_list():
        node_health_stats[node].append(states[node])


def record_result_as_subgraph(average_type_health, network, result_graph, stage):
    result_graph.add_subgraph(stage)
    # Add nodes with HTML-style labels including health and instance count
    for node_id, label in network.get_node_name_to_type_map():
        # Find the instance count by matching the full label
        instance_count = network.get_node_type_instance_count(label)
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
            > network.health_percentage(node_type),
        )
        for node_type in state_counts
    )


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
        healthy_node_states = {node: True for node in network.get_expanded_node_list()}

        attractors = Attractors()
        total_on_states = 0
        total_evaluations = 0
        runs_with_attractor = 0
        runs_no_attractor = 0

        for stage in range(self.num_stages):
            # To store individual node health across runs
            node_health_stats = {node: [] for node in network.get_expanded_node_list()}

            for _ in range(self.num_runs_per_stage):
                (
                    total_evaluations,
                    total_on_states,
                    attractor_found,
                ) = self.run_single_simulation(
                    attractors,
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
            attractors, runs_with_attractor, runs_no_attractor
        )
        result_text.print_kauffman_parameters(k, max_k, n, p)

        if attractors.count() < 20:
            print("Creating attractor graph")
            create_attractor_graph(attractors, network)

        result_graph.add_info_box(k, max_k, n, p)
        return p, attractors.count()

    def run_single_simulation(
        self,
        attractors,
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
        for _ in range(self.num_steps_per_run):
            states = network.update_states(states)

            # Update the counters for P value calculation
            total_on_states += sum(states.values())
            total_evaluations += len(states)

            current_state = normalize_attractor(frozenset(states.items()), network)
            if current_state in state_history:
                attractor_index = state_history.index(current_state)
                attractor_sequence = state_history[attractor_index:]
                attractor_found = True
                break

            state_history.append(current_state)
        evaluate_and_update_health(network, node_health_stats, states)
        if attractor_found:
            # Process the found attractor sequence
            attractors.update_attractor_counts(attractor_sequence)
        return total_evaluations, total_on_states, attractor_found


def create_attractor_graph(attractors, network):
    attractor_graph = AttractorGraph(network, attractors.total_runs())

    for attractor, count in attractors.items():
        attractor_graph.add_attractor(attractor, count)

    attractor_graph.write("attractors_graph.dot")


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
