import random


# Define the Boolean functions
def all_func(inputs):
    return all(inputs)


def none_func(inputs):
    return not any(inputs)


def one_func(inputs):
    return any(inputs)


def percentage_func(percentage):
    def perc_func(inputs):
        return sum(inputs) >= len(inputs) * (percentage / 100)

    return perc_func


def xor_func(inputs):
    return sum(inputs) % 2 == 1


def majority_func(inputs):
    return sum(inputs) > len(inputs) / 2


def random_func(_):  # Underscore is used to indicate that input is ignored
    return random.choice([True, False])


# Function to interpret the function name
def interpret_function(func_name):
    if func_name == "all":
        return all_func
    elif func_name == "none":
        return none_func
    elif func_name == "one":
        return one_func
    elif "%" in func_name:
        percentage = float(func_name.replace("%", ""))
        return percentage_func(percentage)
    elif func_name == "xor":
        return xor_func
    elif func_name == "majority":
        return majority_func
    elif func_name == "random":
        return random_func
    else:
        raise ValueError(f"Unknown function: {func_name}")
