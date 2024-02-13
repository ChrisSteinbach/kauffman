from itertools import combinations
from simulation import Simulation
from kauffman import KauffmanNetwork
from random_network import generate_dot_string
from random_network import generate_network_constraints
import sys
import concurrent
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm


def list_supersets(functions):
    supersets = []
    for i in range(1, len(functions) + 1):
        for combination in combinations(functions, i):
            supersets.append(combination)
    return supersets


def run_simulation(superset, connections, min_instances, max_instances):
    dot_string = generate_dot_string(connections, superset, min_instances, max_instances)
    simulation = Simulation(5)  # Assume this initializes correctly
    network = KauffmanNetwork(dot_string)
    p_value = simulation.run(network)
    p_diff = abs(0.5 - p_value)
    return superset, p_diff


def find_optimal_set(supersets, connections, min_instances, max_instances):
    optimal_p_diff = float('inf')
    optimal_set = None

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_simulation, superset, connections, min_instances, max_instances): superset for
                   superset in supersets}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(supersets), desc="Simulating"):
            superset, p_diff = future.result()
            if p_diff < optimal_p_diff:
                optimal_p_diff = p_diff
                optimal_set = superset

    print("Optimal function set:", optimal_set)


if __name__ == "__main__":
    functions = ["and", "or", "nand", "nor", "xor", "majority", "minority"]
    supersets = list_supersets(functions)

    N = int(sys.argv[1])
    K = int(sys.argv[2])
    min_instances = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    max_instances = int(sys.argv[4]) if len(sys.argv) > 4 else min_instances

    connections = generate_network_constraints(N, K)

    find_optimal_set(supersets, connections, min_instances, max_instances)
