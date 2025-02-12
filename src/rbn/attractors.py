import base64
import hashlib
import re
from collections import defaultdict

import hyperloglog


def short_hash(data):
    serialized = repr(data).encode("utf-8")
    digest = hashlib.sha1(serialized).digest()  # Use SHA-1 for a short hash
    return base64.b32encode(digest)[:8].decode("utf-8")  # Take first 8 chars


def remove_trailing_integer(input_string):
    pattern = r".*\s\d+$"

    # Check if the input string matches the pattern.
    # If it does, remove the last space and the digits following it.
    if re.match(pattern, input_string):
        # The regex here matches a space (\s) followed by one or more digits (\d+) at the end of the string ($)
        # and replaces it with an empty string, effectively removing it.
        return re.sub(r"\s\d+$", "", input_string)

    # If the input string does not match the pattern, return it unchanged
    return input_string


def split_trailing_integer(input_string):
    pattern = r"(.*)\s(\d+)$"

    # Check if the input string matches the pattern.
    # If it does, remove the last space and the digits following it.
    match = re.match(pattern, input_string)
    if match:
        return match.group(1), int(match.group(2))

    raise Exception("Unexpected node instance format: %s" % input_string)


def normalize_attractor(attractor, network):
    node_states_by_type = defaultdict(list)
    for node_id, state in attractor:
        node_type, index = split_trailing_integer(node_id)
        node_states_by_type[node_type].append((index, state))

    # For each node type, sort the (index, state) pairs by index and extract just the state values.
    ordered_states_by_type = {
        node_type: [state for _, state in sorted(indexed_states)]
        for node_type, indexed_states in node_states_by_type.items()
    }

    # Generate a normalized attractor by applying the type_condition to each node type.
    return frozenset(
        (
            node_type,
            network.type_condition(ordered_states_by_type[node_type], node_type),
        )
        for node_type in ordered_states_by_type
    )


class Attractors:
    def __init__(self):
        self._hashes = {}
        self._trigger_events = {}

    def count(self):
        return len(self._trigger_events)

    def total_runs(self):
        return sum(len(hll) for hll in self._trigger_events.values())

    def items(self):
        return tuple((key, len(value)) for key, value in self._trigger_events.items())

    def get_hash(self, attractor_state):
        return self._hashes[attractor_state]

    def update_attractor_counts(self, states, triggering_event):
        attractor_state = normalize_tuple(tuple(states))
        # Create a HyperLogLog counter if needed.
        if attractor_state not in self._trigger_events:
            self._trigger_events[attractor_state] = hyperloglog.HyperLogLog(0.01)
            self._hashes[attractor_state] = short_hash(attractor_state)
        # Record the triggering event (its hash or the event itself)
        self._trigger_events[attractor_state].add(str(hash(triggering_event)))


def normalize_frozenset(frozen_set_instance):
    """Convert frozenset into a sorted tuple for consistent ordering."""
    return tuple(sorted(frozen_set_instance))


def normalize_tuple(cyclic_tuple):
    """Normalize a tuple of frozensets as a cycle."""
    # First, normalize each frozenset to ensure consistent order
    normalized_parts = tuple(
        normalize_frozenset(frozen_set_instance) for frozen_set_instance in cyclic_tuple
    )

    # Generate all rotations of the tuple
    rotations = [
        normalized_parts[i:] + normalized_parts[:i]
        for i in range(len(normalized_parts))
    ]

    # Return the lexicographically smallest rotation
    return min(rotations)
