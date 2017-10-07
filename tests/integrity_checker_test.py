import ast
from unittest import TestCase

from darglint.integrity_checker import IntegrityChecker
from darglint.darglint import get_function_descriptions
from darglint.errors import (
    MissingParameterError,
    MissingReturnError,
    ExcessParameterError,
)


class IntegrityCheckerTestCase(TestCase):

    def test_missing_parameter_added(self):
        program = '''
def function_with_missing_parameter(x):
    """We're missing a description of x."""
    print(x / 2)
'''
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], MissingParameterError))

    def test_excess_parameter_added(self):
        program = '''
def function_with_excess_parameter():
    """We have an extra parameter below, extra.

    Args:
        extra: This shouldn't be here.

    """
    print('Hey!')
'''
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], ExcessParameterError))

    def test_missing_return_parameter_added(self):
        program = '''
def function_without_return():
    """This should have a return in the docstring."""
    global bad_number
    return bad_number
'''
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], MissingReturnError))
