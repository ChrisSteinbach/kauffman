import os
import sys

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pygraphviz as pgv
from matplotlib.colors import ListedColormap, BoundaryNorm


def run(dot_file):
    matplotlib.use("Qt5Agg")
    # Load the DOT file
    network = pgv.AGraph(dot_file)
    # Identify unique node types
    node_types = [node.attr["label"] for node in network.nodes()]

    adj_matrix, matrix_size = create_adjacency_matrix(network, node_types)
    in_degree_scores, out_degree_scores = compute_in_out_degrees(adj_matrix, node_types)

    create_centrality_table(adj_matrix, in_degree_scores, out_degree_scores, node_types)
    show_adjacency_matrix(adj_matrix, matrix_size, node_types)


def create_adjacency_matrix(network, node_types):
    node_type_set = set(node_types)  # To check for existence efficiently
    # Initialize matrix
    type_index = {node_type: i for i, node_type in enumerate(node_types)}
    matrix_size = len(node_types)
    adj_matrix = np.zeros((matrix_size, matrix_size), dtype=int)
    # Populate the adjacency matrix
    for edge in network.edges():
        source_type = edge[0].attr["label"]
        target_type = edge[1].attr["label"]
        if source_type in node_type_set and target_type in node_type_set:
            adj_matrix[type_index[source_type], type_index[target_type]] = 1
    return adj_matrix, matrix_size


def compute_in_out_degrees(adj_matrix, node_types):
    # Compute in-degree and out-degree
    in_degree_scores = {node_type: 0 for node_type in node_types}
    out_degree_scores = {node_type: 0 for node_type in node_types}
    for i, source_type in enumerate(node_types):
        for j, target_type in enumerate(node_types):
            if adj_matrix[i, j] == 1:
                out_degree_scores[source_type] += 1
                in_degree_scores[target_type] += 1
    return in_degree_scores, out_degree_scores


def show_adjacency_matrix(adj_matrix, matrix_size, node_types):
    # -------------------------------------------------------------
    # Create a color matrix to label edges as follows:
    #   0 = no edge
    #   1 = single-direction edge
    #   2 = mutual edge (both directions)
    #   3 = self-loop
    # -------------------------------------------------------------
    color_matrix = np.copy(adj_matrix)
    # Identify mutual edges
    for i in range(matrix_size):
        for j in range(matrix_size):
            if adj_matrix[i, j] == 1 and adj_matrix[j, i] == 1:
                color_matrix[i, j] = 2
                color_matrix[j, i] = 2
    # Identify self-loops
    for i in range(matrix_size):
        if adj_matrix[i, i] == 1:
            color_matrix[i, i] = 3
    # -------------------------------------------------------------
    # Build a colormap for the 4 categories
    # white -> 0, black -> 1, red -> 2, orange -> 3
    # -------------------------------------------------------------
    cmap = ListedColormap(["white", "black", "red", "orange"])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = BoundaryNorm(bounds, cmap.N)
    fig = plt.gcf()
    fig.canvas.manager.set_window_title("Adjacency Matrix")
    # Plot the adjacency matrix using the color matrix
    plt.imshow(color_matrix, cmap=cmap, norm=norm, interpolation="nearest")
    # Add gridlines
    plt.grid(which="both", color="black", linestyle="-", linewidth=0.5)
    # Label ticks
    plt.xticks(ticks=range(matrix_size), labels=node_types, rotation=90)
    plt.yticks(ticks=range(matrix_size), labels=node_types)
    plt.xlabel("Target Node Types")
    plt.ylabel("Source Node Types")
    plt.tight_layout()
    plt.show()


def create_centrality_table(
    adj_matrix, in_degree_scores, out_degree_scores, node_types
):
    # Convert adjacency matrix to a NetworkX graph (optional usage)
    graph = nx.from_numpy_array(np.array(adj_matrix), create_using=nx.DiGraph)
    # Calculate centrality measures
    closeness_centrality = nx.closeness_centrality(graph)
    betweenness_centrality = nx.betweenness_centrality(graph)
    # Map back to your node types

    # Determine the width for the "Node Type" column
    node_type_width = (
        max(len(node_type) for node_type in node_types) + 2
    )  # Adding some padding
    # Combining and formatting centrality scores
    header_format = (
        f"{{:<{node_type_width}}} | {{:^10}} | {{:^10}} | {{:^10}} | {{:^12}}"
    )
    row_format = (
        f"{{:<{node_type_width}}} | {{:^10}} | {{:^10}} | {{:^10.4f}} | {{:^12.4f}}"
    )
    print(
        header_format.format(
            "Node Type", "In-Degree", "Out-Degree", "Closeness", "Betweenness"
        )
    )
    print("-" * (node_type_width + 50))
    for i, node_type in enumerate(node_types):
        in_degree = in_degree_scores[node_type]
        out_degree = out_degree_scores[node_type]
        closeness = closeness_centrality.get(i, 0)
        betweenness = betweenness_centrality.get(i, 0)
        print(
            row_format.format(node_type, in_degree, out_degree, closeness, betweenness)
        )


if __name__ == "__main__":
    # Check if exactly one argument is passed (excluding the script name)
    if len(sys.argv) != 2:
        print("Usage: python adjacency_matrix.py <file.dot>")
        sys.exit(1)

    # Get the filename from the command-line arguments
    dot_file = sys.argv[1]

    # Check if the file has a .dot extension
    if not dot_file.endswith(".dot"):
        print(f"Error: The file '{dot_file}' does not have a .dot extension.")
        sys.exit(1)

    # Check if the file exists
    if not os.path.exists(dot_file):
        print(f"Error: The file '{dot_file}' does not exist.")
        sys.exit(1)

    # File exists and has .dot extension
    print(f"File '{dot_file}' is valid and ready for use.")
    run(dot_file)
