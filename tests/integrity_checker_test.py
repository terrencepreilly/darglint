import ast
from unittest import TestCase

from darglint.integrity_checker import IntegrityChecker
from darglint.darglint import get_function_descriptions
from darglint.errors import (
    ExcessParameterError,
    ExcessRaiseError,
    ExcessYieldError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
)


class IntegrityCheckerTestCase(TestCase):

    def test_missing_parameter_added(self):
        program = '\n'.join([
            'def function_with_missing_parameter(x):',
            '    """We\'re missing a description of x."""',
            '    print(x / 2)',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], MissingParameterError))

    def test_excess_parameter_added(self):
        program = '\n'.join([
            'def function_with_excess_parameter():',
            '    """We have an extra parameter below, extra.',
            '',
            '    Args:',
            '        extra: This shouldn\'t be here.',
            '',
            '    """',
            '    print(\'Hey!\')',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], ExcessParameterError))

    def test_missing_return_parameter_added(self):
        program = '\n'.join([
            'def function_without_return():',
            '    """This should have a return in the docstring."""',
            '    global bad_number',
            '    return bad_number',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], MissingReturnError))

    def test_skips_functions_without_docstrings(self):
        program = '\n'.join([
            'def function_without_docstring(arg1, arg2):',
            '    return 3',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 0)

    def test_missing_yield_added_to_errors(self):
        program = '\n'.join([
            'def funtion_with_yield():',
            '    """This should have a yields section."""',
            '    yield 3',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        self.assertTrue(isinstance(checker.errors[0], MissingYieldError))

    def test_excess_yield_added_to_errors(self):
        program = '\n'.join([
            'def function_with_yield():',
            '    """This should not have a yields section.',
            '',
            '    Yields:',
            '        A number.',
            '',
            '    """',
            '    print(\'Doesnt yield\')',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        self.assertTrue(isinstance(checker.errors[0], ExcessYieldError))

    def test_yields_from_added_to_error(self):
        program = '\n'.join([
            'def function_with_yield():',
            '    """This should have a yields section."""',
            '    yield from (x for x in range(10))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        self.assertTrue(isinstance(checker.errors[0], MissingYieldError))

    def test_missing_raises_added_to_error(self):
        program = '\n'.join([
            'def errorful_function():',
            '    """Should have a raises section here."""',
            '    raise AttributeError',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        error = checker.errors[0]
        self.assertTrue(isinstance(error, MissingRaiseError))
        self.assertEqual(error.name, 'AttributeError')

    # TODO: change to add settings.
    def test_extra_raises_added_to_error(self):
        program = '\n'.join([
            'def non_explicitly_errorful_function(x, y):',
            '    """Should not have a raises section.'
            '',
            '    Args:',
            '        x: The divisor.',
            '        y: The dividend.',
            '',
            '    Raises:',
            '        ZeroDivisionError: If y is zero.',
            '',
            '    Returns:',
            '        The quotient.',
            '',
            '    """',
            '    return x / y',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        error = checker.errors[0]
        self.assertTrue(isinstance(error, ExcessRaiseError))
        self.assertEqual(error.name, 'ZeroDivisionError')

    def has_no_errors(self, program):
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 0)

    def test_noqa_after_excess_raises(self):
        program = '\n'.join([
            'def some_function():',
            '    """Raise an error.',
            '',
            '    Raises:',
            '        Exception: In all cases.  # noqa: I402',
            '',
            '    """',
            '    pass',
        ])
        self.has_no_errors(program)

    def test_noqa_for_missing_raises(self):
        program = '\n'.join([
            'def some_function():',
            '    """No problems.',
            '',
            '    # noqa: I401 Exception',
            '',
            '    """',
            '    raise Exception("No, actually there are problems.")',
        ])
        self.has_no_errors(program)

    def test_noqa_for_excess_parameters(self):
        program = '\n'.join([
            'def excess_arguments():',
            '    """Excess arguments.',
            '',
            '    Args:',
            '        x: Will be here eventually.  # noqa: I102',
            '',
            '    """',
            '    pass'
        ])
        self.has_no_errors(program)

    def test_noqa_for_missing_parameters(self):
        program = '\n'.join([
            'def function_with_missing_parameter(x, y):',
            '    """We\'re missing a description of x, y.',
            '',
            '    # noqa: I101',
            '',
            '    """',
            '    print(x / 2)',
        ])
        self.has_no_errors(program)

    def test_noqa_missing_return_parameter_added(self):
        program = '\n'.join([
            'def function_without_return():',
            '    """This should have a return in the docstring.',
            '',
            '    # noqa: I201',
            '',
            '    """',
            '    global bad_number',
            '    return bad_number',
        ])
        self.has_no_errors(program)

    def test_noqa_excess_return(self):
        program = '\n'.join([
            'def will_be_defined_later():',
            '    """Return will be defined later.',
            '',
            '    Returns:',
            '        Some value yet to be determined.',
            '',
            '    # noqa: I202',
            '',
            '    """',
            '    pass',
        ])
        self.has_no_errors(program)

    def test_noqa_for_missing_yield(self):
        program = '\n'.join([
            'def funtion_with_yield():',
            '    """This should have a yields section.',
            '',
            '    # noqa: I301',
            '',
            '    """',
            '    yield 3',
        ])
        self.has_no_errors(program)

    def test_noqa_for_excess_yield(self):
        program = '\n'.join([
            'def function_with_yield():',
            '    """This should not have a yields section.',
            '',
            '    Yields:',
            '        A number.',
            '',
            '    # noqa: I302',
            '',
            '    """',
            '    print(\'Doesnt yield\')',
        ])
        self.has_no_errors(program)
