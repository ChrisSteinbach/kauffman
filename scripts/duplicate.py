import re
import pygraphviz as pgv
import argparse


def parse_dot(dot_content):
    graph = pgv.AGraph(string=dot_content)
    nodes = {n: dict(graph.get_node(n).attr) for n in graph.nodes()}
    edges = [(e[0], e[1], dict(graph.get_edge(e[0], e[1]).attr)) for e in graph.edges()]
    return graph, nodes, edges


def adjust_func_attribute(func_value, replica_index):
    # Only modify text within parentheses
    return re.sub(
        r"\(([^)]+)\)", lambda m: f"({m.group(1)}_{replica_index})", func_value
    )


def duplicate_graph(graph, nodes, edges, replicas=2):
    new_graph = pgv.AGraph(strict=False, directed=True)

    for name, attrs in nodes.items():
        for i in range(1, replicas + 1):
            new_name = f"{name}_{i}"
            new_label = f"{attrs.get('label', name).replace(' ', '_')}_{i}"
            new_attrs = {
                k: v for k, v in attrs.items() if k != "label"
            }  # Avoid duplicate label argument

            if "func" in new_attrs:
                new_attrs["func"] = adjust_func_attribute(new_attrs["func"], i)

            new_graph.add_node(new_name, label=new_label, **new_attrs)

    for src, dst, attrs in edges:
        for i in range(1, replicas + 1):
            new_src, new_dst = f"{src}_{i}", f"{dst}_{i}"
            new_graph.add_edge(new_src, new_dst, **attrs)

    return new_graph


def main():
    parser = argparse.ArgumentParser(
        description="Duplicate a Graphviz DOT graph with redundancy."
    )
    parser.add_argument("dot_file", type=str, help="Path to the DOT file to process.")
    parser.add_argument(
        "-r", "--replicas", type=int, default=2, help="Number of replicas to create."
    )
    args = parser.parse_args()

    with open(args.dot_file, "r") as file:
        dot_content = file.read()

    graph, nodes, edges = parse_dot(dot_content)
    new_graph = duplicate_graph(graph, nodes, edges, replicas=args.replicas)
    print(new_graph.to_string())


if __name__ == "__main__":
    main()
