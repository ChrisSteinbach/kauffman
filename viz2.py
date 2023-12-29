import pygraphviz as pgv
import numpy as np

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

# Load the DOT file
network = pgv.AGraph("rbn.dot")

# Initialize states randomly
states = {node: np.random.choice([True, False]) for node in network.nodes()}
#states = {node: np.random.choice([True]) for node in network.nodes()}

print(states)

# Initialize the functions array
functions = {node: interpret_function(network.get_node(node).attr['func']) for node in network.nodes()}

# Function to update the state of a node
def update_node_state(node, states, functions, network):
    inputs = [states[neighbor] for neighbor in network.predecessors(node)]
    return functions[node](inputs)

# Simulate the network for a number of steps
num_steps = 10
for step in range(num_steps):
    new_states = states.copy()
    for node in network.nodes():
        new_states[node] = update_node_state(node, states, functions, network)
    states = new_states
    print(f"Step {step}: {states}")

