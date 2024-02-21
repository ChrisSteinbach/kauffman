import random


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


def percentage_func(percentage):
    def perc_func(inputs):
        return sum(inputs) >= len(inputs) * (percentage / 100)

    return perc_func


def xor_func(inputs):
    return sum(inputs) % 2 == 1


def majority_func(inputs):
    return sum(inputs) > len(inputs) / 2


def minority_func(inputs):
    return sum(inputs) > len(inputs) / 2


def random_func(_):  # Underscore is used to indicate that input is ignored
    return random.choice([True, False])

def copy_func(inputs):  # Underscore is used to indicate that input is ignored
    if len(inputs):
      return inputs[0]

# Function to interpret the function name and return the corresponding function
def interpret_function(func_name):
    if func_name == "all":
        return and_func
    elif func_name == "none":
        return nor_func  # 'none' true only if all inputs are false, similar to NOR
    elif func_name == "one":
        # This previously represented a function that returns True if at least one input is True, similar to OR
        return or_func
    elif func_name == "and":
        return and_func
    elif func_name == "or":
        return or_func
    elif func_name == "xor":
        return xor_func
    elif func_name == "nand":
        return nand_func
    elif func_name == "nor":
        return nor_func
    elif "%" in func_name:
        percentage = float(func_name.replace("%", ""))
        return percentage_func(percentage)
    elif func_name == "majority":
        return majority_func
    elif func_name == "minority":
        return minority_func
    elif func_name == "random":
        return random_func
    elif func_name == "copy":
        return copy_func
    else:
        raise ValueError(f"Unknown function: {func_name}")
