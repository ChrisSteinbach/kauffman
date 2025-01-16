#!/usr/bin/python
import random
import numpy as np
import re
from rbn import kauffman
import os
import time
import curses

def debug_message(message):
    with open("/tmp/debug.log", "a") as log_file:
        log_file.write(f"{message}\n")

def initialise_node_states(network):

    # Prepare a list of nodes that can potentially fail, excluding health indicators
    potential_nodes_to_fail = [node for node in network.expanded_network if
                               node not in network.get_health_indicator_nodes()]

    states = {node: True for node in network.expanded_network}

    # Introduce failures randomly among the potential nodes
    nodes_to_fail = random.sample(potential_nodes_to_fail, random.randint(0, len(potential_nodes_to_fail)))
    for node in nodes_to_fail:
        states[node] = False

    return states


def update_node_state(node, states, functions, expanded_network, input_types):
    inputs = [states[neighbor] for neighbor in expanded_network[node]]
    types = [input_types[neighbor] for neighbor in expanded_network[node]]
    #return functions[node](inputs)
    return functions[node](inputs, types)

def update_states(expanded_network, network, states):
    # Update states based on Boolean functions and adjusted P values
    new_states = states.copy()
    for node in expanded_network:
        new_states[node] = update_node_state(node, states, network.functions, expanded_network, network.input_types)
    return new_states

def display_columns(stdscr, states_history, node_states, terminal_width, padding):
    """Displays the columns of state history within the terminal width."""
    # Determine the number of rows and columns to display
    num_columns = min(len(states_history), terminal_width - padding)  # Adjust for row numbers
    row_names = {}
    index = 0
    for key, value in node_states.items():
        row_names[index] = key
        index = index + 1

    # Define color pairs for 1 and 0 states
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_GREEN)  # Green for True
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_RED)    # Red for False


    # Print the states row by row with row numbers
    for row in range(len(states_history[0])):
        row_name = row_names[row]
        row_number = f"{row + 1} ({row_name})".ljust(padding) + ":"
        stdscr.addstr(row, 0, row_number)
        for col in range(-num_columns, 0):
           state = states_history[col][row]
           color = curses.color_pair(1 if state else 2)
           stdscr.addstr(row, padding + col + num_columns - 1, ' ', color)

def list_node_states(node_states):
    current_state = []
    for key, value in node_states.items():
        current_state.append(value)
    return current_state

def parse_input(input_buffer):
    """Parses the input buffer to extract numbers and ranges."""
    result = []
    parts = input_buffer.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
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
    expanded_network = network.expanded_network
    node_states = initialise_node_states(network)
    current_state = list_node_states(node_states)
    states_history = [current_state]

    # Get terminal dimensions
    terminal_width = curses.COLS
    max_row_number = len(current_state)
    max_name_length = 0
    for name in node_states.keys():
        if len(name) > max_name_length:
            max_name_length = len(name)
    padding = len(str(max_row_number)) + max_name_length + 4  # Space for row number and extra space

    # Input buffer for multi-digit numbers
    input_buffer = ""

    while True:
        # Display the state history as columns without clearing the screen
        display_columns(stdscr, states_history, node_states, terminal_width, padding)

        # Display the prompt at the bottom
        stdscr.move(len(current_state) + 2, 0)
        stdscr.clrtoeol()  # Clear the line before writing
        stdscr.addstr(len(current_state) + 2, 0, "Enter row numbers separated by commas (or ranges with '-') to flip states (or 'q' to quit): ")
        
        stdscr.move(len(current_state) + 3, 0)
        stdscr.clrtoeol()  # Clear the line before writing stdscr.addstr(f"Input: {input_buffer}")
        stdscr.addstr(f"Input: {input_buffer}")

        try:
            # Get user input
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter key
                # Parse and process the input buffer
                rows_to_flip = parse_input(input_buffer)
                for row_index in rows_to_flip:
                    if 0 <= row_index < len(current_state):
                        current_state[row_index] = not current_state[row_index]
                index = 0
                for key, value in node_states.items():
                    node_states[key] = current_state[index]
                    index = index + 1

                input_buffer = ""  # Clear the buffer after processing
            elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
                input_buffer = input_buffer[:-1]  # Remove last character
            elif 48 <= key <= 57 or key in (44, 45):  # Digits (0-9), comma, or hyphen
                input_buffer += chr(key)

        except Exception:
            pass

        # Generate a new state and add it to the history
        node_states = update_states(expanded_network, network, node_states)
        current_state = list_node_states(node_states)
        states_history.append(current_state)

        # Maintain only the required number of columns for scrolling
        if len(states_history) > terminal_width - 5:  # Adjust for row numbers
            states_history.pop(0)

        # Refresh the screen
        stdscr.refresh()

        # Pause slightly before the next iteration
        time.sleep(0.2)


def random_sim_kauffman(stdscr):
    network = kauffman.KauffmanNetwork("plg_example.dot")
    loop(stdscr, network)

if __name__ == "__main__":
    curses.wrapper(random_sim_kauffman)
