import numpy as np

# Define the number of nodes in the network
num_nodes = 100

# Generate random initial states for these nodes
states = np.random.choice([0, 1], size=num_nodes)

# Define a function to update the state of the nodes
def update_states(current_states):
    new_states = np.zeros_like(current_states)
    for i in range(len(current_states)):
        # For this example, let's say the state of each node is determined
        # by the XOR of its two neighbors, wrapping around the ends of the array
        left_neighbor = current_states[i-1]
        right_neighbor = current_states[(i+1) % num_nodes]
        new_states[i] = left_neighbor ^ right_neighbor
    return new_states

# Now we simulate the network over some iterations
num_iterations = 50
for _ in range(num_iterations):
    states = update_states(states)
    print(states)

