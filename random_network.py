import random
import sys


def generate_network_constraints(N, K, max_attempts=1000):
    nodes = [f"N{i}" for i in range(N)]
    connections = set()
    incoming = {node: 0 for node in nodes}
    outgoing = {node: 0 for node in nodes}
    attempts = 0

    while attempts < max_attempts:
        source = random.choice(nodes)
        target = random.choice(nodes)
        # Check if adding this connection keeps both nodes within the K limit
        if source != target and (outgoing[source] + incoming[source]) < K and (outgoing[target] + incoming[target]) < K:
            connections.add((source, target))
            incoming[target] += 1
            outgoing[source] += 1
            attempts = 0  # Reset attempts after a successful connection
        else:
            attempts += 1  # Increment attempts after a failed connection attempt

    return connections


def write_dot_file(filename, connections, func_name, min_instances=1, max_instances=1):
    with open(filename, 'w') as f:
        f.write("digraph RBN {\n")
        nodes = set([source for source, _ in connections] + [target for _, target in connections])
        for node in nodes:
            instances = random.randint(min_instances, max_instances)
            f.write(f'    {node} [label="{node}", func="{func_name}", instances={instances}];\n')
        for source, target in connections:
            f.write(f'    {source} -> {target};\n')
        f.write("}\n")


if __name__ == "__main__":
    if len(sys.argv) < 5 or len(sys.argv) > 7:
        print("Usage: python script.py <dot_filename> <N> <K> <func_name> [<min_instances> <max_instances>]")
        sys.exit(1)

    dot_filename = sys.argv[1]
    N = int(sys.argv[2])
    K = int(sys.argv[3])
    func_name = sys.argv[4]
    min_instances = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    max_instances = int(sys.argv[6]) if len(sys.argv) > 6 else min_instances

    connections = generate_network_constraints(N, K)
    write_dot_file(dot_filename, connections, func_name, min_instances, max_instances)
