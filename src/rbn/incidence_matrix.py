import numpy as np


def build_incidence_matrix_from_attractor_counts(attractor_counts):
    """
    Build an incidence matrix for attractors listed in attractor_counts.
    (Same approach as before.)
    """
    # 1) Gather all unique node names across all attractors
    all_nodes = set()
    for states_tuple, _count in attractor_counts:
        for state in states_tuple:
            for node_name, value in state:
                all_nodes.add(node_name)
    node_list = sorted(all_nodes)

    # 2) Initialize the incidence matrix
    incidence = np.zeros((len(attractor_counts), len(node_list)), dtype=int)

    # 3) Fill the incidence matrix
    for i, (states_tuple, _count) in enumerate(attractor_counts):
        # Collect possible values for each node across all states in this attractor
        node_values = {n: set() for n in node_list}
        for state in states_tuple:
            for node_name, val in state:
                node_values[node_name].add(val)

        # If a node is always False, mark it as failed
        for j, node_name in enumerate(node_list):
            if node_values[node_name] == {False}:
                incidence[i, j] = 1

    return incidence, node_list



def build_html_table(incidence, node_list, network):
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
    html = []
    html.append('<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">')

    # Header row
    html.append("<TR>")
    html.append("<TD><B>Attractor</B></TD>")
    for node_name in node_list:
        node_label = network.get_node_label(node_name)
        html.append(f"<TD><B>{node_label}</B></TD>")
    html.append("<TD><B>RowTotal</B></TD>")
    html.append("</TR>")

    # Incidence rows
    for i in range(num_attractors):
        html.append("<TR>")
        # Row label
        html.append(f"<TD>Attr #{i+1}</TD>")
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


if __name__ == "__main__":
    # Sample data, mirroring your example structure
    attractor_counts = [
        (((("A", True), ("B", True), ("C", True), ("D", True)),), 2512),
        (((("A", True), ("B", False), ("C", True), ("D", True)),), 815),
        (
            (
                (("A", False), ("B", True), ("C", True), ("D", False)),
                (("A", True), ("B", True), ("C", False), ("D", True)),
            ),
            1650,
        ),
        (
            (
                (("A", False), ("B", False), ("C", True), ("D", False)),
                (("A", True), ("B", False), ("C", False), ("D", True)),
            ),
            1690,
        ),
        (((("A", False), ("B", True), ("C", False), ("D", False)),), 825),
        (((("A", False), ("B", False), ("C", False), ("D", False)),), 24508),
    ]

    # 1) Build the incidence matrix
    incidence_matrix, node_list = build_incidence_matrix_from_attractor_counts(
        attractor_counts
    )

    # 2) Print a nicely formatted table
    print_incidence_table(incidence_matrix, node_list)
