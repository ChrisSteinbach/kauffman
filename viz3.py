import pygraphviz as pgv
import numpy as np
import random

# Define the Boolean functions
def all_func(inputs):
    return all(inputs)

def none_func(inputs):
    return not any(inputs)

def one_func(inputs):
    return any(inputs)

def percentage_func(percentage):
    def func(inputs):
        return sum(inputs) >= len(inputs) * (percentage / 100)
    return func

# Function to interpret the function name from the DOT file
def interpret_function(func_name):
    if func_name == "all":
        return all_func
    elif func_name == "none":
        return none_func
    elif func_name == "one":
        return one_func
    elif "%" in func_name:
        percentage = float(func_name.replace("%", ""))
        return percentage_func(percentage)
    else:
        raise ValueError(f"Unknown function: {func_name}")

# Function to update the state of a node
def update_node_state(node, states, functions, network):
    inputs = [states[neighbor] for neighbor in network.predecessors(node)]
    return functions[node](inputs)

# Function to evaluate network health
def evaluate_network_health(states, health_indicator_nodes):
    return sum(states[node] for node in health_indicator_nodes) / len(health_indicator_nodes)

# Load the DOT file
network = pgv.AGraph("rbn.dot")

# Initialize states
initial_states = {node: True for node in network.nodes()}

# Initialize the functions array
functions = {node: interpret_function(network.get_node(node).attr['func']) for node in network.nodes()}


# Identify health indicator nodes based on their labels
health_indicator_nodes = [node for node in network.nodes() if network.get_node(node).attr['label'].startswith("Health")]


# Simulation parameters
num_stages = 10
num_runs_per_stage = 20
num_steps_per_run = 20

for stage in range(num_stages):
    health_sum = 0

    for run in range(num_runs_per_stage):
        # Reset states to healthy at the start of each run
        states = initial_states.copy()

        # Introduce failures randomly
        nodes_to_fail = random.sample(network.nodes(), k=stage)
        for node in nodes_to_fail:
            states[node] = False

        # Run the simulation for this stage
        for step in range(num_steps_per_run):
            new_states = states.copy()
            for node in network.nodes():
                new_states[node] = update_node_state(node, states, functions, network)
            states = new_states
            # print(f"Step {step}: {states}")

        # Evaluate network health
        health_sum += evaluate_network_health(states, health_indicator_nodes)

    # Calculate average health for this stage
    average_health = health_sum / num_runs_per_stage
    print(f"Stage {stage}: Average Network Health = {average_health}")

