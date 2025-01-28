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

    # Prepare a list of nodes that can potentially fail, excluding health indicators
    potential_nodes_to_fail = network.get_expanded_node_list()

    states = {node: True for node in network.get_expanded_node_list()}

    # Introduce failures randomly among the potential nodes
    nodes_to_fail = random.sample(
        potential_nodes_to_fail, random.randint(0, len(potential_nodes_to_fail))
    )
    for node in nodes_to_fail:
        states[node] = False

    return states


def display_columns(stdscr, states_history, node_states, terminal_width, padding):
    """Displays the columns of state history within the terminal width."""
    # Determine the number of rows and columns to display
    num_columns = min(
        len(states_history), terminal_width - padding
    )  # Adjust for row numbers
    row_names = {}
    index = 0
    for key, _ in node_states.items():
        row_names[index] = key
        index = index + 1

    # Define color pairs for 1 and 0 states
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_GREEN)  # Green for True
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)  # Red for False

    # Print the states row by row with row numbers
    for row in range(len(states_history[0])):
        row_name = row_names[row]
        row_number = f"{row + 1} ({row_name})".ljust(padding) + ":"
        stdscr.addstr(row, 0, row_number)
        for col in range(-num_columns, 0):
            state = states_history[col][row]
            color = curses.color_pair(1 if state else 2)
            stdscr.addstr(row, padding + col + num_columns - 1, " ", color)


def list_node_states(node_states):
    current_state = []
    for value in node_states.values():
        current_state.append(value)
    return current_state


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

    # Get terminal dimensions
    terminal_width = curses.COLS
    max_row_number = len(current_state)
    max_name_length = reduce(lambda x, y: max(x, len(y)), node_states.keys(), 0)

    padding = (
        len(str(max_row_number)) + max_name_length + 4
    )  # Space for row number and extra space

    # Input buffer for multi-digit numbers
    input_buffer = ""

    while True:
        # Display the state history as columns without clearing the screen
        display_columns(stdscr, states_history, node_states, terminal_width, padding)

        # Display the prompt at the bottom
        stdscr.move(len(current_state) + 2, 0)
        stdscr.clrtoeol()  # Clear the line before writing
        stdscr.addstr(
            len(current_state) + 2,
            0,
            "Row numbers separated by commas or ranges with '-' flip states, 'q' to quit, 'a' for all, 'n' for none: ",
        )

        stdscr.move(len(current_state) + 3, 0)
        stdscr.clrtoeol()  # Clear the line before writing stdscr.addstr(f"Input: {input_buffer}")
        stdscr.addstr(f"Input: {input_buffer}")

        try:
            # Get user input
            key = stdscr.getch()

            if key == ord("q"):
                break

            if key == ord("a"):
                # Set all nodes to True
                for key in node_states.keys():
                    node_states[key] = True

            if key == ord("n"):
                # Set all nodes to False
                for key in node_states.keys():
                    node_states[key] = False

            if key in (curses.KEY_ENTER, 10, 13):  # Enter key
                # Parse and process the input buffer
                rows_to_flip = parse_input(input_buffer)
                for row_index in rows_to_flip:
                    if 0 <= row_index < len(current_state):
                        current_state[row_index] = not current_state[row_index]
                index = 0
                for key in node_states.keys():
                    node_states[key] = current_state[index]
                    index = index + 1

                input_buffer = ""  # Clear the buffer after processing
            elif key in (curses.KEY_BACKSPACE, 127):  # Backspace key
                input_buffer = input_buffer[:-1]  # Remove last character
            elif 48 <= key <= 57 or key in (44, 45):  # Digits (0-9), comma, or hyphen
                input_buffer += chr(key)

        except Exception:
            pass

        # Generate a new state and add it to the history
        node_states = network.update_states(node_states)
        current_state = list_node_states(node_states)
        states_history.append(current_state)

        # Maintain only the required number of columns for scrolling
        if len(states_history) > terminal_width - 5:  # Adjust for row numbers
            states_history.pop(0)

        # Refresh the screen
        stdscr.refresh()

        # Pause slightly before the next iteration
        time.sleep(0.2)


DOT_FILE = None


def random_sim_kauffman(stdscr):
    network = kauffman.KauffmanNetwork(DOT_FILE)
    loop(stdscr, network)


if __name__ == "__main__":
    # Check if exactly one argument is passed (excluding the script name)
    if len(sys.argv) != 2:
        print("Usage: python perturbations.py <file.dot>")
        sys.exit(1)

    # Get the filename from the command-line arguments
    DOT_FILE = sys.argv[1]

    # Check if the file has a .dot extension
    if not DOT_FILE.endswith(".dot"):
        print(f"Error: The file '{DOT_FILE}' does not have a .dot extension.")
        sys.exit(1)

    # Check if the file exists
    if not os.path.exists(DOT_FILE):
        print(f"Error: The file '{DOT_FILE}' does not exist.")
        sys.exit(1)

    # File exists and has .dot extension
    print(f"File '{DOT_FILE}' is valid and ready for use.")
    curses.wrapper(random_sim_kauffman)
