import unittest
from rbn.attractors import split_trailing_integer


class TestAttractors(unittest.TestCase):

    def test_split_trailing_integer(self):
        a, one = split_trailing_integer("a 1")
        self.assertEqual(a, "a")
        self.assertEqual(1, one)


if __name__ == "__main__":
    unittest.main()
