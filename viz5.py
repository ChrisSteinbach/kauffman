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
    def perc_func(inputs):
        return sum(inputs) >= len(inputs) * (percentage / 100)
    return perc_func

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


# Load the DOT file
network = pgv.AGraph("rbn.dot")

# Initialize the functions for each node
functions = {node: interpret_function(network.get_node(node).attr['func']) for node in network.nodes()}

# Identify health indicator nodes based on their labels
health_indicator_nodes = [node for node in network.nodes() if network.get_node(node).attr['label'].startswith("Health")]

# Extract node labels for readable output
node_labels = {node: network.get_node(node).attr['label'] for node in network.nodes()}

# Initialize states to True (healthy)
initial_states = {node: True for node in network.nodes()}

# Simulation parameters
num_stages = 5
num_runs_per_stage = 5
num_steps_per_run = 5

# Function to update the state of a node
def update_node_state(node, states, functions, network):
    inputs = [states[neighbor] for neighbor in network.predecessors(node)]
    print(f"function {functions[node].__name__}  node[{node}] inputs[{inputs}]")
    return functions[node](inputs)

# Function to evaluate network health
def evaluate_network_health(states, health_indicator_nodes):
    return sum(states[node] for node in health_indicator_nodes) / len(health_indicator_nodes)

# To store individual node health across runs
node_health_stats = {node: [] for node in network.nodes()}

for stage in range(num_stages):
    health_sum = 0

    for run in range(num_runs_per_stage):
        states = initial_states.copy()

        # Introduce failures randomly
        nodes_to_fail = random.sample(network.nodes(), k=stage)
        for node in nodes_to_fail:
            states[node] = False

        # Run the simulation for this stage
        print()
        print(f"Init 0: {states}")
        for step in range(num_steps_per_run):
            new_states = states.copy()
            for node in network.nodes():
                new_states[node] = update_node_state(node, states, functions, network)
            states = new_states
            print(f"Step {step}: {states}")

        # Evaluate network health
        print(f"Final step {step}: {states}")
        health_sum += evaluate_network_health(states, health_indicator_nodes)

        # Update individual node health
        for node in network.nodes():
            node_health_stats[node].append(states[node])

    # Calculate average health for this stage
    average_health = health_sum / num_runs_per_stage
    #for node, health in node_health_stats.items():
        #print("Node:" + node)
        #print(health)
    average_node_health = {node_labels[node]: np.mean(health) for node, health in node_health_stats.items()}

    print(f"Stage {stage}: Average Network Health = {average_health}")
    print("Average Health of Individual Nodes:")
    for node, health in average_node_health.items():
        print(f"  {node}: {health}")

