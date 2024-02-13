from itertools import combinations

from simulation import Simulation
from kauffman import KauffmanNetwork
from random_network import generate_dot_string
from random_network import generate_network_constraints
import sys


def list_supersets(functions):
    supersets = []
    for i in range(1, len(functions) + 1):
        for combination in combinations(functions, i):
            supersets.append(combination)
    return supersets


functions = ["and", "or", "nand", "nor", "xor", "majority", "minority"]
supersets = list_supersets(functions)

N = int(sys.argv[1])
K = int(sys.argv[2])
min_instances = int(sys.argv[3]) if len(sys.argv) > 3 else 1
max_instances = int(sys.argv[4]) if len(sys.argv) > 4 else min_instances

connections = generate_network_constraints(N, K)

# Assume generate_dot_string and list_supersets are defined as discussed

# Initialize variables and structures
optimal_p_diff = float('inf')
optimal_set = None

for superset in supersets:
    dot_string = generate_dot_string(connections, superset, min_instances, max_instances)
    simulation = Simulation(5)  # Initialize Simulation with the network
    network = KauffmanNetwork(dot_string)  # Initialize KauffmanNetwork with string
    p_value = simulation.run(network)  # Run the simulation and get P value

    # Calculate the difference from the target P value (0.5)
    p_diff = abs(0.5 - p_value)
    if p_diff < optimal_p_diff:
        optimal_p_diff = p_diff
        optimal_set = superset

# Post-processing: print the optimal function set
print("Optimal function set:", optimal_set)

