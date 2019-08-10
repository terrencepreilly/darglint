import ast
from unittest import (
    TestCase,
)

from darglint.config import Configuration
from darglint.docstring.base import DocstringStyle
from darglint.integrity_checker import IntegrityChecker
from darglint.function_description import get_function_descriptions
from darglint.errors import (
    EmptyDescriptionError,
    ExcessParameterError,
    ExcessRaiseError,
    ExcessVariableError,
    ExcessYieldError,
    GenericSyntaxError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
    MissingDocstringForPublicFunction,
    MissingDocstringForPublicMethod,
    ParameterTypeMismatchError,
    ReturnTypeMismatchError,
)
from darglint.parse.common import ParserException


class IntegrityCheckerSphinxTestCase(TestCase):

    def setUp(self):
        self.config = Configuration(
            ignore=[],
            message_template=None,
            style=DocstringStyle.SPHINX,
            raise_on_missing_docstrings=False
        )

    def test_missing_parameter(self):
        """Make sure we capture missing parameters."""
        program = '\n'.join([
            'def cons(x, l):',
            '    """Add an item to the head of the list.',
            '    ',
            '    :param x: The item to add to the list.',
            '    :return: The list with the item attached.',
            '    ',
            '    """',
            '    return [x] + l',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors]
        )
        self.assertTrue(isinstance(errors[0], MissingParameterError))

    def test_variable_doesnt_exist(self):
        """Ensure described variables must exist in the function."""
        program = '\n'.join([
            'def circle_area(r):',
            '    """Calculate the circle\'s area.',
            '    ',
            '    :param r: The radius of the circle.',
            '    :var pi: An estimate of PI.',
            '    :return: The area of the circle.',
            '    ',
            '    """',
            '    return 3.1415 * r**2',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors]
        )
        self.assertTrue(isinstance(errors[0], ExcessVariableError))
        self.assertEqual(errors[0].terse_message, '+v pi')


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

    def test_try_block_no_excess_error(self):
        """Make sure the else and except blocks are checked.

        See Issue 20.

        """
        program = '\n'.join([
            'def check_module_installed(name):',
            '    """Temp',
            '    ',
            '    Args:',
            '        name (str): module name',
            '    ',
            '    Returns:',
            '        bool: Whether the module can be imported',
            '    ',
            '    """',
            '    try:',
            '        __import__(name)',
            '    except ImportError:',
            '        return False',
            '    else:',
            '        return True',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 0)

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
            '    """Should not have a raises section.',
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
        self.assertEqual(
            len(checker.errors), 1,
            checker.errors
        )
        error = checker.errors[0]
        self.assertTrue(isinstance(error, ExcessRaiseError))
        self.assertEqual(error.name, 'ZeroDivisionError')

    def test_arg_types_checked_if_in_both_docstring_and_function(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    """Get the square root of the number.',
            '',
            '    Args:',
            '        x (float): The number to root.',
            '',
            '    Returns:',
            '        float: The square root',
            '',
            '    """',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        error = checker.errors[0]
        self.assertTrue(isinstance(error, ParameterTypeMismatchError))
        self.assertEqual(error.expected, 'int')
        self.assertEqual(error.actual, 'float')

    def test_return_type_unchecked_if_not_defined_in_docstring(self):
        program = '\n'.join([
            'def foo() -> str:',
            '    """Just a foobar.',
            '',
            '    Returns:',
            '        bar',
            '',
            '    """',
            '    return "bar"',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 0)

    def test_return_type_unchecked_if_not_defined_in_function(self):
        program = '\n'.join([
            'def foo():',
            '    """Just a foobar.',
            '',
            '    Returns:',
            '        str: bar',
            '',
            '    """',
            '    return "bar"',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 0)

    def test_return_type_checked_if_defined_in_docstring_and_function(self):
        program = '\n'.join([
            'def update_model(x: dict) -> dict:',
            '    """Update the model represented by the dictionary.',
            '',
            '    Args:',
            '        x (dict): The dictionary to update.',
            '',
            '    Returns:',
            '        list: The updated dictionary.',
            '',
            '    """',
            '    x.update({"data": 3})',
            '    return x',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(len(checker.errors), 1)
        error = checker.errors[0]
        self.assertTrue(isinstance(error, ReturnTypeMismatchError))
        self.assertEqual(error.expected, 'dict')
        self.assertEqual(error.actual, 'list')

    def has_no_errors(self, program):
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        self.assertEqual(
            len(checker.errors),
            0,
            'Expected there to be no errors, but there were {}'.format(
                len(checker.errors)
            )
        )

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

    def test_noqa_for_parameter_type_mismatch(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    """Get the square root of the number.',
            '',
            '    Args:',
            '        x (float): The number to root.',
            '',
            '    Returns:',
            '        float: The square root',
            '',
            '    # noqa: I103',
            '',
            '    """',
            '    return x ** 0.5',
        ])
        self.has_no_errors(program)

    def test_noqa_for_parameter_type_mismatch_by_name(self):
        program = '\n'.join([
            'def square_root(x: int, y: int) -> float:',
            '    """Get the square root of the number.',
            '',
            '    Args:',
            '        x (float): The number to root.',
            '        y (int): Something else.',
            '',
            '    Returns:',
            '        float: The square root',
            '',
            '    # noqa: I103 x',
            '',
            '    """',
            '    return x ** 0.5',
        ])
        self.has_no_errors(program)

    def test_noqa_for_return_type_mismatch(self):
        program = '\n'.join([
            'def update_model(x: dict) -> dict:',
            '    """Update the model represented by the dictionary.',
            '',
            '    Args:',
            '        x (dict): The dictionary to update.',
            '',
            '    Returns:',
            '        list: The updated dictionary.',
            '',
            '    # noqa: I203',
            '',
            '    """',
            '    x.update({"data": 3})',
            '    return x',
        ])
        self.has_no_errors(program)

    def test_incorrect_syntax_raises_exception_optionally(self):
        # example taken from https://github.com/deezer/html-linter
        program = '\n'.join([
            'def lint(html, exclude=None):',
            '    """Lints and HTML5 file.',
            '',
            '    Args:',
            '      html: str the contents of the file.',
            '      exclude: optional iterable with the Message classes',
            '               to be ommited from the output.',
            '    """',
            '    exclude = exclude or []',
            '    messages = [m.__unicode__() for m in HTML5Linter(html',
            '        ).messages',
            '                if not isinstance(m, tuple(exclude))]',
            '    return \'\\n\'.join(messages)',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(raise_errors=True)

        with self.assertRaises(ParserException):
            checker.run_checks(functions[0])

        # The default is to not raise exceptions.
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertTrue(isinstance(errors[0], GenericSyntaxError))

    def test_throws_assertion_if_no_colon_in_parameter_line(self):
        program = '\n'.join([
            'def hash_integer(value):',
            '    """Return the hash value of an integer.',
            '',
            '    Args:',
            '        value: The integer that we want',
            # This line should cause an error because it is at the
            # level for parameter identifiers.
            '        to make a hashed value of.',
            '',
            '    Returns:',
            '        The hashed value.',
            '',
            '    """',
            '    return value % 7',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)

        checker = IntegrityChecker(raise_errors=True)

        with self.assertRaises(ParserException):
            checker.run_checks(functions[0])

        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertTrue(isinstance(errors[0], GenericSyntaxError))

    def test_throws_assertion_if_no_content_after_colon(self):
        program = '\n'.join([
            'def hello_world(name):',
            '    """Tell the person hello.',
            '',
            '    Args:',
            '        name:',
            '',
            '    """',
            '    print("Hello, {}".format(name))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(raise_errors=True)

        with self.assertRaises(ParserException):
            checker.run_checks(functions[0])

        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertTrue(isinstance(errors[0], EmptyDescriptionError))

    def test_bare_noqa(self):
        program = '\n'.join([
            'def is_palindrome(word):',
            '    """Return True if is palindrome.',
            '',
            '    # noqa',
            '',
            '    """',
            '    return word == word[::-1]',
        ])
        self.has_no_errors(program)

    def test_global_noqa(self):
        program = '\n'.join([
            'def is_palindrome(word):',
            '    """Return True if is palindrome.',
            '',
            '    # noqa: *',
            '',
            '    """',
            '    return word == word[::-1]',
        ])
        self.has_no_errors(program)

    def test_global_noqa_works_for_syntax_errors(self):
        program = '\n'.join([
            'def test_dataframe(input):',
            '    """Test.',
            '',
            '    Args:',
            '        input (:obj:`DataFrame <pandas.DataFrame>`, \\',
            '            :obj:`ndarray <numpy.ndarray>`, list): test',
            '',
            '    {}',
            '',
            '    """',
            '    pass',
        ])
        for variant in ['# noqa: *', '# noqa: S001', '# noqa']:
            self.has_no_errors(program.format(variant))

        self.config = Configuration(
            ignore=[],
            message_template=None,
            style=DocstringStyle.SPHINX,
            raise_on_missing_docstrings=False
        )

    def test_check_for_missing_docstrings(self):
        """Make sure we capture missing parameters."""
        program = '\n'.join([
            # Function without a docstring.
            'def foo():',
            '    pass',
            # Function with a docstring.
            'def bar():',
            '    """"docstring"""',
            '    pass',
            # private function without a docstring.
            'def _foo():',
            '    pass',
            'class FooBar:',
            # Method with a docstring.
            '    def bar_method(self):',
            '        """docstring"""',
            '        pass',
            # Method without a docstring.
            '    def foo_method(self):',
            '        pass',
            # Private method without a docstring.
            '    def _foo_method(self):',
            '        pass',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)

        # No errors if raise_on_missing_docstrings is False.
        checker = IntegrityChecker(
            Configuration(
                ignore=[],
                message_template=None,
                style=DocstringStyle.GOOGLE,
                raise_on_missing_docstrings=False
            )
        )
        for f in functions:
            checker.run_checks(f)
        errors = checker.errors
        self.assertEqual(len(errors), 0)

        # But two errors if True.
        checker = IntegrityChecker(
            Configuration(
                ignore=[],
                message_template=None,
                style=DocstringStyle.GOOGLE,
                raise_on_missing_docstrings=True
            )
        )
        for f in functions:
            checker.run_checks(f)
        errors = checker.errors
        self.assertEqual(len(errors), 2)

        # Somehow the functions are parsed methods -> functions.
        self.assertTrue(isinstance(
            errors[0], MissingDocstringForPublicMethod))
        self.assertTrue(isinstance(
            errors[1], MissingDocstringForPublicFunction))
        self.assertEqual(errors[0].general_message,
                         'Missing docstring for public method')
        self.assertEqual(errors[0].terse_message,
                         'foo_method')
        self.assertEqual(errors[1].general_message,
                         'Missing docstring for public function')
        self.assertEqual(errors[1].terse_message,
                         'foo')
