import random
import re


# Define the Boolean functions
def all_func(inputs, _):
    return all(inputs)


def and_func(inputs, _):
    return all(inputs)


def or_func(inputs, _):
    return any(inputs)


def nand_func(inputs, _):
    return not all(inputs)


def nor_func(inputs, _):
    return not any(inputs)


def percentage_func(inputs, percentage):
    return sum(inputs) >= len(inputs) * (percentage / 100)


def xor_func(inputs, _):
    return sum(inputs) % 2 == 1


def majority_func(inputs, _):
    return sum(inputs) >= len(inputs) / 2


def minority_func(inputs, _):
    return sum(inputs) < len(inputs) / 2


def random_func(inputs, _):
    choices = [True, False]
    if len(inputs) > 0:
        choices = [bool(value) for value in inputs]
    return random.choice(choices)


def copy_func(inputs, _):
    if len(inputs):
        return inputs[0]


def true_func(inputs, _):
    return True


def false_func(inputs, _):
    return False


function_map = {
    "all": all_func,
    "and": and_func,
    "nand": nand_func,
    "or": or_func,
    "nor": nor_func,
    "xor": xor_func,
    "none": nor_func,
    "one": or_func,
    "majority": majority_func,
    "minority": minority_func,
    "random": random_func,
    "copy": copy_func,
    "true": true_func,
    "false": false_func,
    "%": percentage_func,  # Special case for percentages
}


def filter_by_modulo(inputs, modulo, group_index):
    results = []
    for i in range(len(inputs)):
        if i % modulo == group_index:
            results.append(inputs[i])
    return results


def interpret_function(func_str):
    """
    Parse the function string and return a function that evaluates it.
    Supports grouping with parentheses, in addition to AND (&) and OR (|).
    Conditions can be global (e.g. "one", "50%") or type-specific.
    The new syntax is:
         <func>(<target_type>, mod=<modulo>, group=<group_index>)
    For example:
         75%(A, mod=2, group=0)
         majority(B, mod=3, group=2)
    """

    def group_input_types(input_types, inputs, target_type):
        return [inputs[i] for i, t in enumerate(input_types) if t == target_type]

    def evaluate(condition, inputs):
        if "%" in condition:
            percentage = int(condition.replace("%", ""))
            return function_map["%"](inputs, percentage)
        elif condition in function_map:
            return function_map[condition](inputs, None)
        else:
            raise ValueError(f"Unknown function: {condition}")

    def evaluate_condition(condition, inputs, input_types):
        # Try to match the new syntax with parameters:
        # e.g., "75%(A, mod=2, group=0)" or "majority(B, mod=3, group=2)"
        new_regex = r"(\w+|\d+%)\(\s*([A-Za-z0-9_]+)\s*(?:,\s*mod\s*=\s*(\d+)\s*,\s*group\s*=\s*(\d+))?\s*\)"
        match = re.match(new_regex, condition)
        if match:
            func, target_type, modulo, group_index = match.groups()
            if modulo is not None:
                modulo = int(modulo)
                group_index = int(group_index)
                filtered_inputs = filter_by_modulo(inputs, modulo, group_index)
            else:
                # No modulo parameters; select all inputs for the target type.
                filtered_inputs = [
                    inputs[i] for i, t in enumerate(input_types) if t == target_type
                ]
            return evaluate(func, filtered_inputs)
        else:
            # If no parentheses (or no comma parameters) are present, treat as a global condition.
            return evaluate(condition, inputs)

    def tokenize(expr):
        token_specification = [
            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("AND", r"&"),
            ("OR", r"\|"),
            ("SKIP", r"\s+"),
            # A condition token is any run of characters that doesn't include whitespace,
            # &, |, or parentheses; it may also include an optional parenthesized part.
            ("COND", r"[^&|\(\)\s]+(?:\([^&|\(\)]*\))?"),
        ]
        tok_regex = "|".join(
            f"(?P<{name}>{pattern})" for name, pattern in token_specification
        )
        tokens = []
        for mo in re.finditer(tok_regex, expr):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "SKIP":
                continue
            tokens.append((kind, value))
        return tokens

    def parse_expr(tokens):
        node, tokens = parse_term(tokens)
        while tokens and tokens[0][0] == "OR":
            tokens.pop(0)  # consume OR token
            right, tokens = parse_term(tokens)
            node = ("OR", node, right)
        return node, tokens

    def parse_term(tokens):
        node, tokens = parse_factor(tokens)
        while tokens and tokens[0][0] == "AND":
            tokens.pop(0)  # consume AND token
            right, tokens = parse_factor(tokens)
            node = ("AND", node, right)
        return node, tokens

    def parse_factor(tokens):
        if not tokens:
            raise ValueError("Unexpected end of tokens")
        token = tokens.pop(0)
        if token[0] == "LPAREN":
            node, tokens = parse_expr(tokens)
            if not tokens or tokens[0][0] != "RPAREN":
                raise ValueError("Missing closing parenthesis")
            tokens.pop(0)  # Remove RPAREN
            return node, tokens
        elif token[0] == "COND":
            return ("COND", token[1]), tokens
        else:
            raise ValueError("Unexpected token: " + str(token))

    tokens = tokenize(func_str)
    parse_tree, remaining_tokens = parse_expr(tokens)
    if remaining_tokens:
        raise ValueError("Unexpected tokens remaining: " + str(remaining_tokens))

    def eval_tree(tree, inputs, input_types):
        node_type = tree[0]
        if node_type == "COND":
            condition_str = tree[1]
            return evaluate_condition(condition_str, inputs, input_types)
        elif node_type == "AND":
            return eval_tree(tree[1], inputs, input_types) and eval_tree(
                tree[2], inputs, input_types
            )
        elif node_type == "OR":
            return eval_tree(tree[1], inputs, input_types) or eval_tree(
                tree[2], inputs, input_types
            )
        else:
            raise ValueError("Unknown tree node type: " + str(node_type))

    def node_function(inputs, input_types):
        return eval_tree(parse_tree, inputs, input_types)

    return node_function
