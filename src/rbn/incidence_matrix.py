import numpy as np


def build_incidence_matrix_from_attractor_counts(attractors, network):
    """
    Build an incidence matrix for attractors listed in attractor_counts.
    """
    attractor_counts = attractors.items()
    node_list = network.get_node_types()

    # Initialize the incidence matrix
    incidence = np.zeros((len(attractor_counts), len(node_list)), dtype=int)
    attractor_ids = {}

    # Fill the incidence matrix
    for i, (states_tuple, _count) in enumerate(attractor_counts):
        # Collect possible values for each node across all states in this attractor
        attractor_ids[i] = attractors.get_hash(states_tuple)
        node_values = {n: set() for n in node_list}
        for state in states_tuple:
            for node_name, val in state:
                node_values[node_name].add(val)

        # If a node is always False, mark it as failed
        for j, node_name in enumerate(node_list):
            if node_values[node_name] == {False}:
                incidence[i, j] = 1

    return incidence, attractor_ids


def build_html_table(incidence, attractor_ids, network):
    """
    Returns a string containing the HTML <TABLE> snippet
    for embedding in a Graphviz dot file.
    """
    num_attractors, num_nodes = incidence.shape

    # Compute row sums and column sums if you like
    row_sums = incidence.sum(axis=1)
    col_sums = incidence.sum(axis=0)
    grand_total = row_sums.sum()

    # Start building the table
    html = [
        '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">',
        "<TR>",
        "<TD><B>Attractor</B></TD>",
    ]

    # Header row
    for node_name in network.get_node_types():
        node_label = network.get_node_label(node_name)
        html.append(f"<TD><B>{node_label}</B></TD>")
    html.append("<TD><B>RowTotal</B></TD>")
    html.append("</TR>")

    # Incidence rows
    for i in range(num_attractors):
        html.append("<TR>")
        # Row label
        html.append(f"<TD>#{attractor_ids[i]}</TD>")
        # Each cell
        for j in range(num_nodes):
            val = incidence[i, j]
            html.append(f"<TD>{val}</TD>")
        # Row total
        html.append(f"<TD>{row_sums[i]}</TD>")
        html.append("</TR>")

    # Totals row
    html.append("<TR>")
    html.append("<TD><B>Totals</B></TD>")
    for j in range(num_nodes):
        html.append(f"<TD><B>{col_sums[j]}</B></TD>")
    html.append(f"<TD><B>{grand_total}</B></TD>")
    html.append("</TR>")

    html.append("</TABLE>")
    return "".join(html)
