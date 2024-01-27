import matplotlib.pyplot as plt
import numpy as np
import pygraphviz as pgv
import networkx as nx

# Function to determine if a node is a "Health" node
def is_health_node(node_label):
    return node_label.startswith("Health")

# Load the DOT file
network = pgv.AGraph("plg_example.dot")

# Step 1: Identify unique node types
# Assume network is your PyGraphviz graph
node_types = [node.attr['label'] for node in network.nodes() if not is_health_node(node.attr['label'])]
node_type_set = set(node_types)  # To check for existence efficiently

# Step 2: Initialize matrix
type_index = {node_type: i for i, node_type in enumerate(node_types)}
matrix_size = len(node_types)
adj_matrix = np.zeros((matrix_size, matrix_size), dtype=int)

# Populate the adjacency matrix, excluding health nodes
for edge in network.edges():
    source_type = edge[0].attr['label']
    target_type = edge[1].attr['label']
    if source_type in node_type_set and target_type in node_type_set:
        adj_matrix[type_index[source_type], type_index[target_type]] = 1

# Assume adj_matrix is your adjacency matrix and node_types is a list of node types
in_degree_scores = {node_type: 0 for node_type in node_types}
out_degree_scores = {node_type: 0 for node_type in node_types}

for i, source_type in enumerate(node_types):
    for j, target_type in enumerate(node_types):
        if adj_matrix[i, j] == 1:
            out_degree_scores[source_type] += 1
            in_degree_scores[target_type] += 1

# Convert adjacency matrix to a NetworkX graph
G = nx.from_numpy_array(np.array(adj_matrix), create_using=nx.DiGraph)

# Calculate centrality measures
closeness_centrality = nx.closeness_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)


# Map back to your node types
node_type_list = list(node_types)
mapped_closeness = {node_type_list[i]: centrality for i, centrality in closeness_centrality.items()}
mapped_betweenness = {node_type_list[i]: centrality for i, centrality in betweenness_centrality.items()}


# Determine the width for the "Node Type" column
node_type_width = max(len(node_type) for node_type in node_types) + 2  # Adding some padding

# Combining and formatting centrality scores
header_format = f"{{:<{node_type_width}}} | {{:^10}} | {{:^10}} | {{:^10}} | {{:^12}}"
row_format = f"{{:<{node_type_width}}} | {{:^10}} | {{:^10}} | {{:^10.4f}} | {{:^12.4f}}"

print(header_format.format("Node Type", "In-Degree", "Out-Degree", "Closeness", "Betweenness"))
print("-" * (node_type_width + 50))

for i, node_type in enumerate(node_types):
    in_degree = in_degree_scores[node_type]
    out_degree = out_degree_scores[node_type]
    closeness = closeness_centrality.get(i, 0)
    betweenness = betweenness_centrality.get(i, 0)
    print(row_format.format(node_type, in_degree, out_degree, closeness, betweenness))


# Visualize the matrix
plt.imshow(adj_matrix, cmap='Greys', interpolation='nearest')

# Add gridlines for clarity
plt.grid(which='both', color='black', linestyle='-', linewidth=0.5)

# Add labels for clarity
plt.xticks(ticks=range(len(node_types)), labels=node_types, rotation=90)
plt.yticks(ticks=range(len(node_types)), labels=node_types)

plt.title("Adjacency Matrix")
plt.xlabel("Target Node Types")
plt.ylabel("Source Node Types")
plt.show()
