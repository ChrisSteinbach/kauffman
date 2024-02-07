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
    else:
        raise ValueError(f"Unknown function: {func_name}")
