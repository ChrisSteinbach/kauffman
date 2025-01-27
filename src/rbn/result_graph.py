import pygraphviz as pgv


def create_info_box_label(N, K, MAX_K, P):
    return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD>N (Total Nodes): {N}</TD></TR><TR><TD>K (Avg. Inputs per Node): {K:.2f}</TD></TR><TR><TD>K (Max Inputs per Node): {MAX_K:.2f}</TD></TR><TR><TD>P (Bias in Boolean Functions): {P}</TD></TR></TABLE>>'


def is_health_node(node_label):
    return node_label.startswith("Health")


def create_html_label(label, health, instance_count):
    health_percentage = f"{health * 100:.1f}%"
    return f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4"><TR><TD>{label}</TD></TR><TR><TD>Health: {health_percentage}</TD></TR><TR><TD>Instances: {instance_count}</TD></TR></TABLE>>'


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


def fix_node_alignment(master_graph_dot, num_stages):
    # Dynamically generate the alignment snippet based on the number of stages
    # Create align_X node declarations with style=invis
    align_node_declarations = "\n\t\t".join(
        [f"align_{i} [style=invis];" for i in range(num_stages)]
    )
    # Create align_X -> align_Y edges with style=invis
    align_edges = (
        " -> ".join([f"align_{i}" for i in range(num_stages)]) + " [style=invis];"
    )
    # Complete alignment snippet
    alignment_snippet = f"""
    \tsubgraph align {{
            \tgraph [rankdir=LR];
            \t{align_node_declarations}
            \trank=same {align_edges}
    }}
    """
    # Edges from align_X to invisible_X
    for i in range(num_stages):
        alignment_snippet += f"\n\talign_{i} -> invisible_{i} [style=invis];"
    # Insert the alignment snippet before the last closing brace
    modified_dot_content = (
        master_graph_dot.rsplit("}", 1)[0] + alignment_snippet + "}\n"
    )
    return modified_dot_content


class ResultGraph:
    def __init__(self):
        self.master_graph = pgv.AGraph(strict=True, directed=True, compound=True)
        self.stage_graph = None

    def add_subgraph(self, stage):
        self.stage_graph = self.master_graph.add_subgraph(
            name=f"cluster_{stage}", label=f"Random failures = {stage}"
        )

        # Add an invisible node to this subgraph for ordering an alignment
        invisible_node_id = f"invisible_{stage}"
        self.stage_graph.add_node(invisible_node_id, style="invis")

    def add_node(self, node_id, stage, label, health, instance_count):
        fill_color = get_node_color(health)  # Calculate graduated color
        html_label = create_html_label(label, health, instance_count)

        # Set penwidth and border color based on whether it's a "Health" node
        penwidth = 3 if is_health_node(label) else 1
        border_color = "black" if is_health_node(label) else fill_color

        # Prefix node ID with stage number
        prefixed_node_id: str = f"{stage}_{node_id}"
        self.stage_graph.add_node(
            prefixed_node_id,
            label=html_label,
            shape="rectangle",
            color=border_color,
            fillcolor=fill_color,
            style="filled",
            penwidth=penwidth,
        )

    def add_edge(self, edge, stage):
        prefixed_source_id = f"{stage}_{edge[0]}"
        prefixed_target_id = f"{stage}_{edge[1]}"
        self.stage_graph.add_edge(prefixed_source_id, prefixed_target_id)

    # Function to create HTML-like label for the info box
    def add_info_box(self, K, MAX_K, N, P):
        # Add an info box node
        info_box_label = create_info_box_label(N, K, MAX_K, P)
        self.master_graph.add_node(
            "info_box",
            label=info_box_label,
            shape="note",
            style="filled",
            color="lightgrey",
        )

    def write(self, num_stages, filename):
        # Output the combined master graph to a file
        master_graph_dot = self.master_graph.to_string()
        modified_dot_content = fix_node_alignment(master_graph_dot, num_stages)
        # Writing to the file
        with open(filename, "w") as file:
            file.write(modified_dot_content)


class NullResultGraph:
    def add_subgraph(self, stage):
        pass

    def add_node(self, node_id, stage, label, health, instance_count):
        pass

    def add_edge(self, edge, stage):
        pass

    # Function to create HTML-like label for the info box
    def add_info_box(self, K, MAX_K, N, P):
        pass

    def write(self, num_stages, filename):
        pass
