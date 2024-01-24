import pygraphviz as pgv
import numpy as np
import random

# Define the Boolean functions
def all_func(inputs):
    return all(inputs)

def none_func(inputs):
    return not any(inputs)

def one_func(inputs):
    return any(inputs)

def percentage_func(percentage):
    def perc_func(inputs):
        return sum(inputs) >= len(inputs) * (percentage / 100)
    return perc_func

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

# Function to dynamically adjust P values based on network conditions
def adjust_p_values(node, expanded_network, states, base_p_values):
    # Example: decrease P value if a node has more than a threshold of failing downstream nodes
    threshold = 0.5
    downstream_nodes = expanded_network[node]
    if downstream_nodes:
        failing_downstream = sum(not states[down] for down in downstream_nodes) / len(downstream_nodes)
        if failing_downstream > threshold:
            return max(base_p_values[node] * (1 - failing_downstream), 0)  # Adjust P value based on failure rate
    return base_p_values[node]


# Load the DOT file
network = pgv.AGraph("plg_example.dot")


# Create a mapping from labels to original node identifiers
original_label_map = {}
for node in network.nodes():
    original_label_map[node.name] = node.attr['label']

def get_node_color(health):
    if health > 0.5:
        # More green as health increases
        green_intensity = int(255 * health)
        red_intensity = 255 - green_intensity
    else:
        # More red as health decreases
        red_intensity = int(255 * (1 - health))
        green_intensity = 255 - red_intensity

    return f"#{red_intensity:02x}{green_intensity:02x}00"  # RGB color


# Initialize an empty dictionary to store instance counts
instance_counts = {}

# Iterate over nodes in the original network to count instances
for node in network.nodes():
    node_type = node.attr['label']  # or node.name, depending on your structure
    # Assuming the number of instances is stored in a node attribute 'instances'
    instance_count = int(node.attr.get('instances', 1))  # Default to 1 if 'instances' attribute is not found
    instance_counts[node_type] = instance_count


# Expand nodes based on 'instances' attribute and apply functions
expanded_network = {}
functions = {}
for node in network.nodes():
    num_instances = int(node.attr['instances'])
    func = interpret_function(node.attr['func'])
    for i in range(1, num_instances + 1):
        instance_name = f"{node.attr['label']} {i}"
        expanded_network[instance_name] = []
        functions[instance_name] = func

# Expand connections based on expanded nodes
for edge in network.edges():
    source_instances = [n for n in expanded_network if n.startswith(edge[0].attr['label'])]
    target_instances = [n for n in expanded_network if n.startswith(edge[1].attr['label'])]
    for source in source_instances:
        for target in target_instances:
            if source != target:  # Exclude self-connections
              expanded_network[source].append(target)

# Initialize states to True (healthy)
initial_states = {node: True for node in expanded_network}

def update_node_state(node, states, functions, expanded_network):
    # If the node is already unhealthy, it remains unhealthy
    if not states[node]:
        return False

    # Otherwise, update its state based on the inputs and its function
    inputs = [states[neighbor] for neighbor in expanded_network[node]]
    return functions[node](inputs)

# Function to evaluate network health
def evaluate_network_health(states, health_indicator_nodes):
    return sum(states[node] for node in health_indicator_nodes) / len(health_indicator_nodes)

# Identify health indicator nodes based on their labels
health_indicator_nodes = [node for node in expanded_network if node.startswith("Health")]

# Simulation parameters
num_stages = 5
num_runs_per_stage = 2000
num_steps_per_run = 20

# N - Total Number of Nodes
N = len(expanded_network)

# K - Average Number of Inputs per Node
total_inputs = sum(len(neighbors) for neighbors in expanded_network.values())
K = total_inputs / N if N > 0 else 0

total_on_states = 0
total_evaluations = 0

# Function to determine if a node is a "Health" node
def is_health_node(node_label):
    return node_label.startswith("Health")

# Function to create HTML-like label with health status and instance count
def create_html_label(label, health, instance_count):
    health_percentage = f"{health * 100:.1f}%"
    return f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4"><TR><TD>{label}</TD></TR><TR><TD>Health: {health_percentage}</TD></TR><TR><TD>Instances: {instance_count}</TD></TR></TABLE>>'


# Initialize a master graph
master_graph = pgv.AGraph(strict=True, directed=True, compound=True)



for stage in range(num_stages):

    # To store individual node health across runs
    node_health_stats = {node: [] for node in expanded_network}

    # Initialize base P values for each node type (modify as per your actual functions)
    base_p_values = {node: 1.0 for node in expanded_network}  # Example base P values

    health_sum = 0

    for run in range(num_runs_per_stage):
        states = initial_states.copy()

        # Prepare a list of nodes that can potentially fail, excluding health indicators
        potential_nodes_to_fail = [node for node in expanded_network if node not in health_indicator_nodes]

        # Introduce failures randomly among the potential nodes
        nodes_to_fail = random.sample(potential_nodes_to_fail, min(len(potential_nodes_to_fail), stage))
        for node in nodes_to_fail:
            states[node] = False

        # Run the simulation for this stage
        #print()
        #print(f"Init 0: {states}")
        for step in range(num_steps_per_run):
            # Dynamically adjust P values at each step
            current_p_values = {node: adjust_p_values(node, expanded_network, states, base_p_values)
                                for node in expanded_network}


            # Update states based on Boolean functions and adjusted P values
            new_states = states.copy()
            for node in expanded_network:
                if not states[node]:  # Node remains failed if already failed
                    continue
                else:
                    # First, determine state based on Boolean function
                    new_states[node] = functions[node]([states[neighbor] for neighbor in expanded_network[node]])
            
                    # Then, modify state based on current P value (additional layer of logic)
                    if np.random.rand() >= current_p_values[node]:
                        new_states[node] = False  # Override state to False based on P value
            states = new_states
            #print(f"Step {step}: {states}")
                    # Update the counters for P value calculation
            total_on_states += sum(states.values())
            total_evaluations += len(states)

        # Evaluate network health and update individual node health
        #print(f"Final step {step}: {states}")
        health_sum += evaluate_network_health(states, health_indicator_nodes)
        #print(f"Health sum {health_sum}")
        for node in expanded_network:
            node_health_stats[node].append(states[node])

    # Calculate average health for this stage
    average_health = health_sum / num_runs_per_stage

    # Group and calculate average health by node type
    type_health_stats = {}
    for node in node_health_stats:
        node_type = ' '.join(node.split()[:-1])  # Extract node type from instance name
        if node_type not in type_health_stats:
            type_health_stats[node_type] = []
        type_health_stats[node_type].extend(node_health_stats[node])

    average_type_health = {node_type: np.mean(healths) for node_type, healths in type_health_stats.items()}

    print(f"\nStage {stage}: Average Network Health = {average_health}")
    print("Average Health of Node Types:")
    for node_type, health in average_type_health.items():
        print(f"  {node_type}: {health}")

    stage_graph = master_graph.add_subgraph(name=f"cluster_{stage}", label=f"Random failures = {stage}")
    # Add nodes with HTML-style labels including health and instance count
    for node_id, label in original_label_map.items():
        # Find the instance count by matching the full label
        instance_count = instance_counts.get(label, 1)  # Default to 1 if not found
        health = average_type_health.get(label, 0.5)  # Default health if not found
        fill_color = get_node_color(health)  # Calculate graduated color
        html_label = create_html_label(label, health, instance_count)

        # Set penwidth and border color based on whether it's a "Health" node
        penwidth = 3 if is_health_node(label) else 1
        border_color = "black" if is_health_node(label) else fill_color

        prefixed_node_id = f"{stage}_{node_id}"  # Prefix node ID with stage number
        stage_graph.add_node(prefixed_node_id, label=html_label, shape="rectangle", color=border_color, fillcolor=fill_color, style="filled", penwidth=penwidth)

    # Add edges with prefixed node names
    for edge in network.edges():
        prefixed_source_id = f"{stage}_{edge[0]}"
        prefixed_target_id = f"{stage}_{edge[1]}"
        stage_graph.add_edge(prefixed_source_id, prefixed_target_id)

        # Add an invisible node to this subgraph
    invisible_node_id = f"invisible_{stage}"
    stage_graph.add_node(invisible_node_id, style="invis")

# Add invisible edges between the invisible nodes to influence subgraph order
for stage in range(num_stages - 1):
    master_graph.add_edge(f"invisible_{stage}", f"invisible_{stage + 1}", style="invis")


# At the end of the script, print the Kauffman network parameters
print(f"\nKauffman Network Parameters:")
print(f"N (Total Nodes): {N}")
print(f"K (Average Inputs per Node): {K}")

P = total_on_states / total_evaluations if total_evaluations > 0 else 0

print(f"P (Bias in Boolean Functions): {P}")


# Create a new Graphviz graph
final_graph = pgv.AGraph(strict=True, directed=True)



# Add nodes with HTML-style labels including health and instance count
for node_id, label in original_label_map.items():
    # Find the instance count by matching the full label
    instance_count = instance_counts.get(label, 1)  # Default to 1 if not found
    health = average_type_health.get(label, 0.5)  # Default health if not found
    fill_color = get_node_color(health)  # Calculate graduated color
    html_label = create_html_label(label, health, instance_count)

    # Set penwidth and border color based on whether it's a "Health" node
    if is_health_node(label):
        penwidth = 3
        border_color = "black"  # or any other color that stands out
    else:
        penwidth = 1
        border_color = fill_color

    final_graph.add_node(node_id, label=html_label, shape="rectangle", color=border_color, fillcolor=fill_color, style="filled", penwidth=penwidth)


# Add edges using the original node identifiers
for edge in network.edges():
    final_graph.add_edge(edge[0], edge[1])

# Function to create HTML-like label for the info box
def create_info_box_label(N, K, P):
    return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD>N (Total Nodes): {N}</TD></TR><TR><TD>K (Avg. Inputs per Node): {K:.2f}</TD></TR><TR><TD>P (Bias in Boolean Functions): {P}</TD></TR></TABLE>>'


# Add an info box node
info_box_label = create_info_box_label(N, K, P)
final_graph.add_node("info_box", label=info_box_label, shape="note", style="filled", color="lightgrey")
master_graph.add_node("info_box", label=info_box_label, shape="note", style="filled", color="lightgrey")


# Output the new graph to a file
final_graph.write("final_network_state.dot")


# Output the combined master graph to a file
master_graph.write("combined_stages.dot")
