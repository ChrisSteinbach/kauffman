def print_stage_summary(stage, average_health, average_type_health):
    print(f"\nStage {stage}: Average Network Health = {average_health}")
    print("Average Health of Node Types:")
    for node_type, health in average_type_health.items():
        print(f"  {node_type}: {health}")


def print_kauffman_parameters(K, MAX_K, N, P):
    print(f"\nKauffman Network Parameters:")
    print(f"N (Total Nodes): {N}")
    print(f"K (Average Inputs per Node): {K}")
    print(f"K (Max Inputs per Node): {MAX_K}")
    print(f"P (Bias in Boolean Functions): {P}")


def print_attractor_summary(attractor_counts):
    print("Significant Attractors and their occurrence counts:")
    # Sorting attractors by their count in descending order
    sorted_attractors = sorted(attractor_counts.items(), key=lambda item: item[1], reverse=True)
    for attractor_state, count in sorted_attractors:
        failed_nodes = [node for node, state in attractor_state if not state]
        failed_nodes_str = ', '.join(failed_nodes)
        print(f"Count: {count}, Failed Nodes: {failed_nodes_str}")
