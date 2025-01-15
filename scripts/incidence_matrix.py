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


def print_incidence_table(incidence, node_list):
    """
    Print an ASCII table for the given incidence matrix, showing
    row/column headings and total counts.
    """
    num_attractors, num_nodes = incidence.shape
    row_sums = incidence.sum(axis=1)  # total failed nodes per attractor
    col_sums = incidence.sum(axis=0)  # total failures for each node across attractors
    grand_total = row_sums.sum()

    # Prepare headers: one column for 'Attractor' label, then each node name, then 'RowTotal'
    headers = ["Attractor"] + node_list + ["RowTotal"]

    # Calculate column widths (for a minimal ASCII table)
    # Start with the header widths:
    col_widths = [len(h) for h in headers]

    # Compare with the widths of the incidence data + row_sums
    for i in range(num_attractors):
        # 'Attr #i' length check
        row_label = f"Attr #{i+1}"
        col_widths[0] = max(col_widths[0], len(row_label))
        # Then each incidence value
        for j in range(num_nodes):
            val_str = str(incidence[i, j])
            col_widths[j + 1] = max(col_widths[j + 1], len(val_str))
        # The row sum
        row_sum_str = str(row_sums[i])
        col_widths[-1] = max(col_widths[-1], len(row_sum_str))

    # For the final 'Total' row
    final_row_label = "Totals"
    col_widths[0] = max(col_widths[0], len(final_row_label))
    for j in range(num_nodes):
        col_widths[j + 1] = max(col_widths[j + 1], len(str(col_sums[j])))
    col_widths[-1] = max(col_widths[-1], len(str(grand_total)))

    # Helper: format a row given a list of strings
    def format_row(values):
        return " | ".join(val.rjust(width) for val, width in zip(values, col_widths))

    # Print header row
    print(format_row(headers))
    # Print a separator line
    print("-|-".join("-" * w for w in col_widths))

    # Print each attractor row
    for i in range(num_attractors):
        row_label = f"Attr #{i+1}"
        row_values = [row_label]
        # incidence data
        for j in range(num_nodes):
            row_values.append(str(incidence[i, j]))
        # row total
        row_values.append(str(row_sums[i]))
        print(format_row(row_values))

    # Print the totals row
    totals_row = [final_row_label]
    for j in range(num_nodes):
        totals_row.append(str(col_sums[j]))
    totals_row.append(str(grand_total))
    print(format_row(totals_row))


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
