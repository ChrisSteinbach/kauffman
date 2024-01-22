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
network = pgv.AGraph("write_path.dot")

# Expand nodes based on 'instances' attribute and apply functions
expanded_network = {}
functions = {}
for node in network.nodes():
    num_instances = int(node.attr['instances'])
    func = interpret_function(node.attr['func'])
    for i in range(1, num_instances + 1):
        instance_name = f"{node.attr['label']} {i}"
        expanded_network[instance_name] = []
        functions[instance_name] = func

# Expand connections based on expanded nodes
for edge in network.edges():
    source_instances = [n for n in expanded_network if n.startswith(edge[0].attr['label'])]
    target_instances = [n for n in expanded_network if n.startswith(edge[1].attr['label'])]
    for source in source_instances:
        for target in target_instances:
            if source != target:  # Exclude self-connections
              expanded_network[source].append(target)

# Initialize states to True (healthy)
initial_states = {node: True for node in expanded_network}

def update_node_state(node, states, functions, expanded_network):
    # If the node is already unhealthy, it remains unhealthy
    if not states[node]:
        return False

    # Otherwise, update its state based on the inputs and its function
    inputs = [states[neighbor] for neighbor in expanded_network[node]]
    return functions[node](inputs)

# Function to evaluate network health
def evaluate_network_health(states, health_indicator_nodes):
    return sum(states[node] for node in health_indicator_nodes) / len(health_indicator_nodes)

# Identify health indicator nodes based on their labels
health_indicator_nodes = [node for node in expanded_network if node.startswith("Health")]

# Simulation parameters
num_stages = 5
num_runs_per_stage = 20
num_steps_per_run = 20

for stage in range(num_stages):
    # To store individual node health across runs
    node_health_stats = {node: [] for node in expanded_network}

    health_sum = 0

    for run in range(num_runs_per_stage):
        states = initial_states.copy()

        # Prepare a list of nodes that can potentially fail, excluding health indicators
        potential_nodes_to_fail = [node for node in expanded_network if node not in health_indicator_nodes]

        # Introduce failures randomly among the potential nodes
        nodes_to_fail = random.sample(potential_nodes_to_fail, min(len(potential_nodes_to_fail), stage))
        for node in nodes_to_fail:
            states[node] = False

        # Run the simulation for this stage
        #print()
        #print(f"Init 0: {states}")
        for step in range(num_steps_per_run):
            new_states = states.copy()
            for node in expanded_network:
                new_states[node] = update_node_state(node, states, functions, expanded_network)
            states = new_states
            #print(f"Step {step}: {states}")

        # Evaluate network health and update individual node health
        #print(f"Final step {step}: {states}")
        health_sum += evaluate_network_health(states, health_indicator_nodes)
        #print(f"Health sum {health_sum}")
        for node in expanded_network:
            node_health_stats[node].append(states[node])

    # Calculate average health for this stage
    average_health = health_sum / num_runs_per_stage
    average_node_health = {node: np.mean(health) for node, health in node_health_stats.items()}

    print(f"Stage {stage}: Average Network Health = {average_health}")
    print("Average Health of Individual Nodes:")
    for node, health in average_node_health.items():
        print(f"  {node}: {health}")

