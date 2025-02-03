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


def interpret_function(func_str):
    """
    Parse the function string and return a function that evaluates it.
    Supports grouping with parentheses, in addition to AND (&) and OR (|).
    Conditions can be global (e.g. "one", "50%") or type-specific (e.g. "one(CPU)").
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
        # Check for type-specific conditions: e.g. one(CPU) or 50%(CPU)
        match = re.match(r"(\w+|\d+%)\(([\w ]+)\)", condition)
        if match:
            func, target_type = match.groups()
            type_inputs = group_input_types(input_types, inputs, target_type)
            return evaluate(func, type_inputs)
        else:
            # Global condition
            return evaluate(condition, inputs)

    # --- Tokenizer ---
    # This simple tokenizer recognizes parentheses, & and | operators, and condition tokens.
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

    # --- Recursive descent parser ---
    # Grammar:
    #   expr   := term ( '|' term )*
    #   term   := factor ( '&' factor )*
    #   factor := COND | '(' expr ')'
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

    # Build the parse tree.
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
