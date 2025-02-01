import base64
import hashlib


def short_hash(data):
    serialized = repr(data).encode("utf-8")
    digest = hashlib.sha1(serialized).digest()  # Use SHA-1 for a short hash
    return base64.b32encode(digest)[:8].decode("utf-8")  # Take first 8 chars


class Attractors:
    def __init__(self):
        self.attractor_counts = {}
        self._hashes = {}

    def count(self):
        return len(self.attractor_counts)

    def total_runs(self):
        return sum(self.attractor_counts.values())

    def items(self):
        return self.attractor_counts.items()

    def get_hash(self, attractor_state):
        return self._hashes[attractor_state]

    def update_attractor_counts(self, states):
        attractor_state = normalize_tuple(tuple(states))
        count = self.attractor_counts.get(attractor_state, 0) + 1
        self.attractor_counts[attractor_state] = count
        if count == 1:
            self._hashes[attractor_state] = short_hash(attractor_state)
        return self.attractor_counts


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
