import pygraphviz as pgv


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


class ResultGraph:
    def __init__(self):
        self.master_graph = pgv.AGraph(strict=True, directed=True, compound=True)
        self.stage_graph = None

    def add_subgraph(self, stage):
        self.stage_graph = self.master_graph.add_subgraph(name=f"cluster_{stage}", label=f"Random failures = {stage}")

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
        self.stage_graph.add_node(prefixed_node_id, label=html_label, shape="rectangle", color=border_color,
                                  fillcolor=fill_color, style="filled", penwidth=penwidth)

    def add_edge(self, edge, stage):
        prefixed_source_id = f"{stage}_{edge[0]}"
        prefixed_target_id = f"{stage}_{edge[1]}"
        self.stage_graph.add_edge(prefixed_source_id, prefixed_target_id)
