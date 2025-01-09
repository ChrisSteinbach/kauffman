from itertools import combinations
from simulation import Simulation
from kauffman import KauffmanNetwork
from random_network import generate_dot_string
from random_network import generate_network_constraints
import sys
import concurrent
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import numpy as np


def list_supersets(functions):
    supersets = []
    for i in range(1, len(functions) + 1):
        for combination in combinations(functions, i):
            supersets.append(combination)
    return supersets


def is_close(a, b, tolerance=0.01):
    return abs(a - b) < tolerance


def run_simulation(superset, N, K, min_instances, max_instances, num_simulations=10):
    max_attractor_count = 0
    for _ in range(num_simulations):
        connections = generate_network_constraints(N, K)
        dot_string = generate_dot_string(connections, superset, min_instances, max_instances)
        network = KauffmanNetwork(dot_string)
        simulation = Simulation(5)  # Assume initialization is correct
        p_value, attractor_count = simulation.run(network)
        max_attractor_count = max(max_attractor_count, attractor_count)
    return superset, max_attractor_count


def find_optimal_set(supersets, N, K, min_instances, max_instances):
    max_attractor_count = 0
    optimal_set = None

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_simulation, superset, N, K, min_instances, max_instances, 10): superset for
                   superset in supersets}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(supersets), desc="Simulating"):
            superset, attractor_count = future.result()
            if attractor_count > max_attractor_count:
                max_attractor_count = attractor_count
                optimal_set = superset

    print("Optimal function set:", optimal_set)


if __name__ == "__main__":
    functions = ["and", "or", "nand", "nor", "xor", "majority", "minority"]
    supersets = list_supersets(functions)

    N = int(sys.argv[1])
    K = int(sys.argv[2])
    min_instances = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    max_instances = int(sys.argv[4]) if len(sys.argv) > 4 else min_instances

    find_optimal_set(supersets, N, K, min_instances, max_instances)
