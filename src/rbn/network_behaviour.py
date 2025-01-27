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
    return sum(inputs) > len(inputs) / 2


def minority_func(inputs, _):
    return sum(inputs) > len(inputs) / 2


def random_func(inputs, _):
    choices = [True, False]
    if len(inputs) > 0:
        choices = [bool(value) for value in inputs]
    return random.choice(choices)


def copy_func(inputs, _):
    if len(inputs):
        return inputs[0]


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
    "%": percentage_func,  # Special case for percentages
}


def interpret_function(func_str):
    """
    Parse the function string and return a function that evaluates it.
    Supports AND (&) and OR (|) between conditions.
    """

    # Function to evaluate a single condition
    def evaluate_condition(condition, inputs, input_types):
        # Check for type-specific conditions
        match = re.match(r"(\w+|\d+%)\(([\w ]+)\)", condition)
        if match:
            func, target_type = match.groups()
            type_inputs = [
                inputs[i] for i, t in enumerate(input_types) if t == target_type
            ]

            if "%" in func:
                percentage = int(func.replace("%", ""))
                return function_map["%"](type_inputs, percentage)
            elif func in function_map:
                return function_map[func](type_inputs, None)
            else:
                raise ValueError(f"Unknown function: {func}")

        # Global conditions
        elif "%" in condition:
            percentage = int(condition.replace("%", ""))
            return function_map["%"](inputs, percentage)
        elif condition in function_map:
            return function_map[condition](inputs, None)
        else:
            raise ValueError(f"Unknown function: {condition}")

    # Parse the function string into conditions with AND (&) and OR (|)
    def node_function(inputs, input_types):
        # Split on OR (|)
        or_conditions = func_str.split("|")
        for or_condition in or_conditions:
            and_conditions = or_condition.split("&")
            # All AND conditions within this OR group must pass
            if all(
                evaluate_condition(cond.strip(), inputs, input_types)
                for cond in and_conditions
            ):
                return True
        # If none of the OR groups pass, return False
        return False

    return node_function
