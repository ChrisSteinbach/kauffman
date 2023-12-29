import pygraphviz as pgv
from itertools import product
import numpy as np

num_iterations = 10

# Step 2: Load the .dot file
network = pgv.AGraph("path_to_network.dot")
num_nodes = network.number_of_nodes()

# Step 3: Initialize the states (randomly in this case)
states = {node: np.random.choice([0, 2]) for node in network.nodes()}

# Step 4: Define a sample update rule (you will need to define your own)
def update_rule(node):
    # In this example, we'll just count the number of active (state == 1) predecessors
    predecessors = network.predecessors(node)
    active_predecessors = sum(states[pred] for pred in predecessors)
    return 1 if active_predecessors >= 2 else 0  # Threshold function

# Step 5: Simulate the network dynamics
for _ in range(num_iterations):
    # Copy the current states
    new_states = states.copy()
    
    # Update states based on the rule
    for node in network.nodes():
        new_states[node] = update_rule(node)
    
    # Log the changes (or visualize them)
    print(new_states)
    
    # Update the states
    states = new_states

