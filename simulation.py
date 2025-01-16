#!/usr/bin/python3.12
import random
import numpy as np
import re
from rbn import kauffman
from rbn.result_graph import ResultGraph, NullResultGraph
from rbn.result_text import ResultText, NullResultText
import sys
import os



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


def record_result_as_subgraph(average_type_health, network, result_graph, stage):
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


def remove_trailing_integer(input_string):
    pattern = r'.*\s\d+$'

    # Check if the input string matches the pattern
    if re.match(pattern, input_string):
        # If it does, remove the last space and the digits following it
        # The regex here matches a space (\s) followed by one or more digits (\d+) at the end of the string ($)
        # and replaces it with an empty string, effectively removing it.
        return re.sub(r'\s\d+$', '', input_string)
    else:
        # If the input string does not match the pattern, return it unchanged
        return input_string


def normalize_attractor(attractor, network):
    # Dict to hold counts of True/False states per node type
    state_counts = {}
    for node_state in attractor:
        node_type, state = remove_trailing_integer(node_state[0]), node_state[1]
        if node_type not in state_counts:
            state_counts[node_type] = {'True': 0, 'False': 0}
        state_counts[node_type][str(state)] += 1

    # Generate a normalized attractor based on state counts as a percentage healthy
    return frozenset(
        f"{node_type} {(state_counts[node_type]['True'] / (state_counts[node_type]['True'] + state_counts[node_type]['False'])) > network.health_percentage[node_type]}"
        for node_type in state_counts)


def update_node_state(node, states, functions, expanded_network, input_types):
    inputs = [states[neighbor] for neighbor in expanded_network[node]]
    types = [input_types[neighbor] for neighbor in expanded_network[node]]
    #return functions[node](inputs)
    return functions[node](inputs, types)

def update_states(expanded_network, network, states):
    # Update states based on Boolean functions and adjusted P values
    new_states = states.copy()
    for node in expanded_network:
        new_states[node] = update_node_state(node, states, network.functions, expanded_network, network.input_types)
    return new_states


class Simulation:
    def __init__(self, num_stages):
        self.num_stages = num_stages
        self.num_runs_per_stage = 2000
        self.num_steps_per_run = 40

    def run(self, network, result_graph=NullResultGraph(), result_text=NullResultText()):
        expanded_network = network.expanded_network

        healthy_node_states = {node: True for node in expanded_network}

        # Identify health indicator nodes based on their labels
        health_indicator_nodes = [node for node in expanded_network if node.startswith("Health")]

        total_on_states = 0
        total_evaluations = 0
        attractor_counts = {}
        runs_with_attractor = 0
        runs_no_attractor = 0

        for stage in range(self.num_stages):
            # To store individual node health across runs
            node_health_stats = {node: [] for node in expanded_network}

            health_sum = 0

            for run in range(self.num_runs_per_stage):
                attractor_counts, health_sum, total_evaluations, total_on_states, attractor_found = self.run_single_simulation(
                    attractor_counts, expanded_network, health_indicator_nodes, health_sum, healthy_node_states,
                    network, node_health_stats, stage, total_evaluations, total_on_states)
                if attractor_found:
                    runs_with_attractor = runs_with_attractor + 1
                else:
                    runs_no_attractor = runs_no_attractor + 1

            # Calculate average health for this stage
            average_health = health_sum / self.num_runs_per_stage
            average_type_health = calculate_average_health_by_type(node_health_stats)

            result_text.print_stage_summary(stage, average_health, average_type_health)
            record_result_as_subgraph(average_type_health, network, result_graph, stage)

        P = total_on_states / total_evaluations if total_evaluations > 0 else 0
        N = network.get_N()
        K = network.get_average_K()
        MAX_K = network.get_max_K()

        result_text.print_attractor_summary(attractor_counts, runs_with_attractor, runs_no_attractor)
        result_text.print_kauffman_parameters(K, MAX_K, N, P)

        if len(attractor_counts) < 10:
            print("Creating attractor graph")
            create_attractor_graph(attractor_counts)


        result_graph.add_info_box(K, MAX_K, N, P)
        return P, len(attractor_counts)

    def run_single_simulation(self, attractor_counts, expanded_network, health_indicator_nodes, health_sum,
                              healthy_node_states, network, node_health_stats, stage, total_evaluations,
                              total_on_states):
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
        health_sum = evaluate_and_update_health(expanded_network, health_indicator_nodes, health_sum,
                                                node_health_stats, states)
        if attractor_found:
            # Process the found attractor sequence
            attractor_counts = self.update_attractor_counts(attractor_counts, attractor_sequence)
        return attractor_counts, health_sum, total_evaluations, total_on_states, attractor_found

    def update_attractor_counts(self, attractor_counts, states):
        # Update attractor counts
        attractor_state = frozenset(states)
        attractor_counts[attractor_state] = attractor_counts.get(attractor_state, 0) + 1
        return attractor_counts

import pygraphviz as pgv

def create_attractor_graph(attractors):
    G = pgv.AGraph(directed=True)
    attractor_id = 0
    for attractor, count in attractors.items():
        subgraph_name = f"cluster_{attractor_id} (Count: {count})"
        subG = G.add_subgraph(name=subgraph_name, label=subgraph_name)
        states = list(attractor)  # Convert frozenset to list for indexing
        for i, state in enumerate(states):
            state_label = ", ".join(state)
            subG.add_node(state_label, label=state_label)
            # Add edge to next state to represent transition
            if len(states) > 1:
                next_state = states[(i + 1) % len(states)]
                next_state_label = ", ".join(next_state)
                subG.add_edge(state_label, next_state_label)
        attractor_id += 1
    G.layout(prog='dot')
    G.write('attractors_graph.dot')

# Assuming attractors is your dictionary of attractors

def random_sim_kauffman(dot_file):
    network = kauffman.KauffmanNetwork(dot_file)
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
