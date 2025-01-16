import random
import re


# Define the Boolean functions
def all_func(inputs):
    return all(inputs)


def and_func(inputs):
    return all(inputs)


def or_func(inputs):
    return any(inputs)


def nand_func(inputs):
    return not all(inputs)


def nor_func(inputs):
    return not any(inputs)


def percentage_func(inputs, percentage):
    return sum(inputs) >= len(inputs) * (percentage / 100)


def xor_func(inputs):
    return sum(inputs) % 2 == 1


def majority_func(inputs):
    return sum(inputs) > len(inputs) / 2


def minority_func(inputs):
    return sum(inputs) > len(inputs) / 2


def random_func(inputs):
    choices = [True, False]
    if len(inputs) > 0:
        choices = [bool(value) for value in inputs]
    return random.choice(choices)

def copy_func(inputs):
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
    "%": percentage_func  # Special case for percentages
}

def interpret_function(func_str):
    """
    Parse the function string and return a function that evaluates it.
    Supports global and type-specific conditions.
    """

    # Parse the function string into conditions
    conditions = func_str.split("&")

    def node_function(inputs, input_types):
        # Evaluate each condition
        for condition in conditions:
            condition = condition.strip()

            # Check for type-specific conditions
            match = re.match(r"(\w+)\((\w+)\)", condition)
            if match:
                func, target_type = match.groups()
                type_inputs = [inputs[i] for i, t in enumerate(input_types) if t == target_type]

                # Handle percentages
                if "%" in func:
                    percentage = int(func.replace("%", ""))
                    if not function_map["%"](type_inputs, percentage):
                        return False
                elif func in function_map:
                    if not function_map[func](type_inputs):
                        return False
                else:
                    raise ValueError(f"Unknown function: {func}")

            # Global conditions
            elif "%" in condition:
                percentage = int(condition.replace("%", ""))
                if not function_map["%"](inputs, percentage):
                    return False
            elif condition in function_map:
                if not function_map[condition](inputs):
                    return False
            else:
                raise ValueError(f"Unknown function: {condition}")

        # If all conditions pass, return True
        return True

    return node_function

