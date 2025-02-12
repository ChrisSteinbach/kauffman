import unittest
from rbn.network_behaviour import interpret_function


class TestInterpretFunction(unittest.TestCase):

    def test_one_global(self):
        """
        Test a simple function string "one" which means
        'True if at least one input is True'.
        """
        func = interpret_function("one")
        # (True, True) => at least one True => result = True
        self.assertTrue(func([False, True], ["X", "Y"]))
        # (False, False) => no True => result = False
        self.assertFalse(func([False, False], ["X", "Y"]))

    def test_all_with_types(self):
        """
        Test a condition "all(A)" which means
        'All inputs of type A must be True' and ignore other types.
        """
        func = interpret_function("all(A)")
        # inputs: [False, True, True], types: [A, A, B]
        # only the first two are type A => we need them both to be True => they are False, True => returns False
        self.assertFalse(func([False, True, True], ["A", "A", "B"]))
        # if the first two are True => function returns True
        self.assertTrue(func([True, True, True], ["A", "A", "B"]))

    def test_percentage_typed(self):
        """
        Test a function like "50%(CPU)" which means
        at least 50% of inputs of type CPU must be True.
        """
        func = interpret_function("50%(CPU)")
        # Suppose we have 3 CPU inputs, 2 of which are True => 2/3 => ~66% => >= 50% => True
        inputs = [True, True, False, True]
        types = ["CPU", "CPU", "CPU", "Memory"]
        self.assertTrue(func(inputs, types))

        # If only 1 of 3 CPU is True => 33% => < 50% => False
        inputs = [True, False, False, False]
        types = ["CPU", "CPU", "CPU", "Memory"]
        self.assertFalse(func(inputs, types))

        # Exaclty 50% => pass
        inputs = [True, True, False, False]
        types = ["CPU", "CPU", "CPU", "CPU"]
        self.assertTrue(func(inputs, types))

    def test_and_combination(self):
        """
        Example with multiple conditions using your custom syntax, e.g. "one(A) & 50%(B)".
        This means: 'At least one input of type A is True' AND 'At least 50% of B-type inputs are True.'
        """
        func = interpret_function("one(A) & 50%(B)")
        # case1: A=[False,True], B=[True, False] => B has 2 inputs, 1 is True => 50% => pass
        # At least one A is True => pass
        # => entire condition => True
        inputs = [False, True, True, False]
        types = ["A", "A", "B", "B"]
        self.assertTrue(func(inputs, types))

        # case2: none of type A is True => fails the 'one(A)' condition
        inputs = [False, False, True, False]
        types = ["A", "A", "B", "B"]
        self.assertFalse(func(inputs, types))

        # case3: A is satisfied but B < 50% => fails
        inputs = [True, False, True, False]
        types = ["A", "A", "B", "B"]
        # A has a True => pass. But among B => 1/2 => 50% => This is exactly 50%.
        self.assertTrue(func(inputs, types))

    def test_or_combination(self):
        """
        Example with multiple conditions using your custom syntax, e.g. "one(A) | 50%(B)".
        This means: 'At least one input of type A is True' OR 'At least 50% of B-type inputs are True.'
        """
        func = interpret_function("one(A) | 50%(B)")
        # case1: A=[False,True], B=[True, False] => B has 2 inputs, 1 is True => 50% => pass
        # At least one A is True => pass
        # => entire condition => True
        inputs = [False, True, True, False]
        types = ["A", "A", "B", "B"]
        self.assertTrue(func(inputs, types))

        # case2: none of type A is True => fails the 'one(A)' condition
        inputs = [False, False, True, False]
        types = ["A", "A", "B", "B"]
        self.assertTrue(func(inputs, types))

        # case3: A is satisfied but B < 50% => fails
        inputs = [True, False, True, False]
        types = ["A", "A", "B", "B"]
        # A has a True => pass. But among B => 1/2 => 50% => This is exactly 50%.
        self.assertTrue(func(inputs, types))

    def test_parentheses_group(self):
        """
        Test that shows parentheses change the outcome even when input data and conditions are otherwise the same
        """
        func = interpret_function("one(A) & (50%(B) | all(C))")

        self.assertFalse(func([False, True, True, True, True], ["A", "B", "B", "C", "C"]))

        func = interpret_function("(one(A) & 50%(B)) | all(C)")

        self.assertTrue(func([False, True, True, True, True], ["A", "B", "B", "C", "C"]))

    def test_modulo_selection(self):
        """
        Test grouped modulo selection
        """

        inputs = [False, True, True, False, True, False]
        types = ["A", "A", "A", "A", "A", "A"]

        func = interpret_function("or(A, mod=3, group=0)")
        self.assertFalse(func(inputs, types))

        func = interpret_function("or(A, mod=2, group=0)")
        self.assertTrue(func(inputs, types))

        func = interpret_function("or(A, mod=3, group=1)")
        self.assertTrue(func(inputs, types))

        func = interpret_function("or(A, mod=3, group=2)")
        self.assertTrue(func(inputs, types))

        func = interpret_function("and(A, mod=3, group=2)")
        self.assertFalse(func(inputs, types))

    def test_xor(self):
        """
        Test a simple function string "xor" which means
        'True if the number of True inputs is odd'.
        """
        func = interpret_function("xor")
        # (True, True) => 2 True => even => result = False
        self.assertFalse(func([True, True], ["X", "Y"]))

        # (False, False) => 2 False => false => result = False
        self.assertFalse(func([False, False], ["X", "Y"]))

        # (True, False) => 1 True => odd => result = True
        self.assertTrue(func([True, False], ["X", "Y"]))

        # (False, True) => 1 True => odd => result = True
        self.assertTrue(func([False, True], ["X", "Y"]))

    def test_nor(self):
        """
        Test a simple function string "nor" which means
        'True if all inputs are False'.
        """
        func = interpret_function("nor")
        # (True, True) => all True => result = False
        self.assertFalse(func([True, True], ["X", "Y"]))
        # (False, False) => all False => result = True
        self.assertTrue(func([False, False], ["X", "Y"]))

    def test_majority(self):
        """
        Test a simple function string "majority" which means
        'True if more than half of the inputs are True'.
        """
        func = interpret_function("majority")
        # (True, True, False) => 2 True, 1 False => result = True
        self.assertTrue(func([True, True, False], ["X", "Y", "Z"]))
        # (True, False, False) => 1 True, 2 False => result = False
        self.assertFalse(func([True, False, False], ["X", "Y", "Z"]))
        # (True, False) => 1 True, 1 False => result = True
        self.assertTrue(func([True, False], ["X", "Y"]))

    def test_minority(self):
        """
        Test a simple function string "minority" which means
        'True if less than half of the inputs are True'.
        """
        func = interpret_function("minority")
        # (True, True, False) => 2 True, 1 False => result = False
        self.assertFalse(func([True, True, False], ["X", "Y", "Z"]))
        # (True, False, False) => 1 True, 2 False => result = True
        self.assertTrue(func([True, False, False], ["X", "Y", "Z"]))
        # (True, False) => 1 True, 1 False => result = False
        self.assertFalse(func([True, False], ["X", "Y"]))

    def test_copy(self):
        """
        Test a simple function string "copy" which means
        'True if the first input is True'.
        """
        func = interpret_function("copy")
        # (True, True) => first True => result = True
        self.assertTrue(func([True, True], ["X", "Y"]))

        # (True, False) => first True => result = True
        self.assertTrue(func([True, False], ["X", "Y"]))

        # (False, False) => first False => result = False
        self.assertFalse(func([False, False], ["X", "Y"]))

        # (False, True) => first False => result = False
        self.assertFalse(func([False, True], ["X", "Y"]))


if __name__ == "__main__":
    unittest.main()
