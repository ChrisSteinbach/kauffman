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

# Function to dynamically adjust P values based on network conditions
def adjust_p_values(node, expanded_network, states, base_p_values):
    # Example: decrease P value if a node has more than a threshold of failing downstream nodes
    threshold = 0.5
    downstream_nodes = expanded_network[node]
    if downstream_nodes:
        failing_downstream = sum(not states[down] for down in downstream_nodes) / len(downstream_nodes)
        if failing_downstream > threshold:
            return max(base_p_values[node] * (1 - failing_downstream), 0)  # Adjust P value based on failure rate
    return base_p_values[node]


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
num_runs_per_stage = 2000
num_steps_per_run = 20

# N - Total Number of Nodes
N = len(expanded_network)

# K - Average Number of Inputs per Node
total_inputs = sum(len(neighbors) for neighbors in expanded_network.values())
K = total_inputs / N if N > 0 else 0

# P - Probability of a Node Being 'On'
# Assuming P is derived from the nature of the Boolean functions
# This is a simplistic calculation and might need to be adjusted based on your functions
# Here, we assume P = 0.5 as a placeholder; modify as needed based on your functions
P = 0.5

for stage in range(num_stages):
    # To store individual node health across runs
    node_health_stats = {node: [] for node in expanded_network}

    # Initialize base P values for each node type (modify as per your actual functions)
    base_p_values = {node: 1.0 for node in expanded_network}  # Example base P values

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
            # Dynamically adjust P values at each step
            current_p_values = {node: adjust_p_values(node, expanded_network, states, base_p_values)
                                for node in expanded_network}


            # Update states based on Boolean functions and adjusted P values
            new_states = states.copy()
            for node in expanded_network:
                if not states[node]:  # Node remains failed if already failed
                    continue
                else:
                    # First, determine state based on Boolean function
                    new_states[node] = functions[node]([states[neighbor] for neighbor in expanded_network[node]])
            
                    # Then, modify state based on current P value (additional layer of logic)
                    if np.random.rand() >= current_p_values[node]:
                        new_states[node] = False  # Override state to False based on P value
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

    # Group and calculate average health by node type
    type_health_stats = {}
    for node in node_health_stats:
        node_type = ' '.join(node.split()[:-1])  # Extract node type from instance name
        if node_type not in type_health_stats:
            type_health_stats[node_type] = []
        type_health_stats[node_type].extend(node_health_stats[node])

    average_type_health = {node_type: np.mean(healths) for node_type, healths in type_health_stats.items()}

    print(f"\nStage {stage}: Average Network Health = {average_health}")
    print("Average Health of Node Types:")
    for node_type, health in average_type_health.items():
        print(f"  {node_type}: {health}")

# At the end of the script, print the Kauffman network parameters
print(f"\nKauffman Network Parameters:")
print(f"N (Total Nodes): {N}")
print(f"K (Average Inputs per Node): {K}")
print(f"P (Bias in Boolean Functions): {P}")
