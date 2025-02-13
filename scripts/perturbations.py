#!/usr/bin/python
import curses
import os
import random
import sys
import time
from functools import reduce

from rbn import kauffman


def debug_message(message):
    with open("/tmp/debug.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"{message}\n")


def initialise_node_states(network):
    return {node: True for node in network.get_expanded_node_list()}


def randomise_node_states(states):
    for node in states.keys():
        states[node] = True

    # introduce failures randomly
    nodes_to_fail = random.sample(list(states.keys()), random.randint(0, len(states)))
    for node in nodes_to_fail:
        states[node] = False
    return states


def display_columns(
    stdscr, states_history, node_states, mask, terminal_width, padding, network
):
    """Displays the columns of state history within the terminal width."""
    num_columns = min(
        len(states_history), terminal_width - padding
    )  # Adjust for row numbers
    row_names = {}
    index = 0
    for key, _ in node_states.items():
        row_names[index] = key
        index += 1

    # Define color pairs for 1 and 0 states
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_GREEN)  # Green for True
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)  # Red for False
    curses.init_pair(
        3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA
    )  # For masked nodes (optional)

    # Print the states row by row with row numbers
    for row in range(len(states_history[0])):
        row_label = network.get_instance_label(row_names[row])
        row_number = f"{row + 1} ({row_label})".ljust(padding)
        stdscr.addstr(row, 0, row_number)
        for col in range(-num_columns, 0):
            state = states_history[col][row]
            masked = mask[row_names[row]]
            color = curses.color_pair(3 if masked else 1 if state else 2)
            stdscr.addstr(row, padding + col + num_columns - 1, " ", color)


def list_node_states(node_states):
    return [value for value in node_states.values()]


def parse_input(input_buffer):
    """Parses the input buffer to extract numbers and ranges."""
    result = []
    parts = input_buffer.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                result.extend(range(start - 1, end))  # Convert to 0-based index
            except ValueError:
                pass  # Ignore invalid ranges
        elif part.isdigit():
            result.append(int(part) - 1)  # Convert to 0-based index
    return result


def loop(stdscr, network):
    # Setup curses
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(True)  # Make getch non-blocking

    # Initial state and history
    node_states = initialise_node_states(network)
    current_state = list_node_states(node_states)
    states_history = [current_state]

    # Initialize a mask dictionary for sticky False states.
    # For each node instance, the mask is initially False.
    mask = {node: False for node in network.get_expanded_node_list()}

    # Get terminal dimensions and compute padding for display
    terminal_width = curses.COLS
    max_row_number = len(current_state)
    node_labels = network.get_instance_labels()
    max_name_length = reduce(lambda x, y: max(x, len(y)), node_labels, 0)
    padding = len(str(max_row_number)) + max_name_length + 4

    # Input buffer for multi-digit numbers
    input_buffer = ""

    while True:
        # Display the state history
        display_columns(
            stdscr, states_history, node_states, mask, terminal_width, padding, network
        )

        # Display the prompt at the bottom
        stdscr.move(len(current_state) + 2, 0)
        stdscr.clrtoeol()
        stdscr.addstr(
            len(current_state) + 2,
            0,
            "Enter rows (e.g. '1,3-5') to flip state, append 'm' to toggle mask, 'r' to randomise, 'q' to quit, 'a' for all, 'n' for none: ",
        )
        stdscr.move(len(current_state) + 3, 0)
        stdscr.clrtoeol()
        stdscr.addstr(f"Input: {input_buffer}")

        try:
            # Get user input
            key = stdscr.getch()
            if key == ord("q"):
                break
            if key == ord("a"):
                for k in node_states.keys():
                    node_states[k] = True
            if key == ord("n"):
                for k in node_states.keys():
                    node_states[k] = False
            if key == ord("r"):
                randomise_node_states(node_states)
            if key == ord("m"):
                mask_input = input_buffer[:]
                rows_to_toggle = parse_input(mask_input)
                for row_index in rows_to_toggle:
                    if 0 <= row_index < len(current_state):
                        # Toggle mask for the corresponding node instance
                        node_key = list(node_states.keys())[row_index]
                        mask[node_key] = not mask[node_key]
                input_buffer = ""
            if key in (curses.KEY_ENTER, 10, 13):  # Enter key
                # Process state flipping normally
                rows_to_flip = parse_input(input_buffer)
                for row_index in rows_to_flip:
                    if 0 <= row_index < len(current_state):
                        current_state[row_index] = not current_state[row_index]
                index = 0
                for k in node_states.keys():
                    node_states[k] = current_state[index]
                    index += 1
                input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127):
                input_buffer = input_buffer[:-1]
            elif (48 <= key <= 57) or key in (44, 45):  # digits, comma, hyphen
                input_buffer += chr(key)
        except Exception:
            pass

        # Update state: generate a new state from the network simulation.
        node_states = network.update_states(node_states)
        # Apply the mask: if a node is masked, force its state to False.
        for k in node_states:
            if mask.get(k, False):
                node_states[k] = False
        current_state = list_node_states(node_states)
        states_history.append(current_state)
        if len(states_history) > terminal_width - 5:
            states_history.pop(0)
        stdscr.refresh()
        time.sleep(0.2)


DOT_FILE = None


def random_sim_kauffman(stdscr):
    network = kauffman.KauffmanNetwork(DOT_FILE)
    loop(stdscr, network)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python perturbations.py <file.dot>")
        sys.exit(1)
    DOT_FILE = sys.argv[1]
    if not DOT_FILE.endswith(".dot"):
        print(f"Error: The file '{DOT_FILE}' does not have a .dot extension.")
        sys.exit(1)
    if not os.path.exists(DOT_FILE):
        print(f"Error: The file '{DOT_FILE}' does not exist.")
        sys.exit(1)
    print(f"File '{DOT_FILE}' is valid and ready for use.")
    curses.wrapper(random_sim_kauffman)
