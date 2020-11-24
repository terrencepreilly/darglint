import ast
from unittest import (
    TestCase,
    skip,
)

from darglint.strictness import Strictness
from darglint.docstring.style import DocstringStyle
from darglint.integrity_checker import (
    IntegrityChecker,
)
from darglint.function_description import (
    get_function_descriptions,
)
from darglint.errors import (
    EmptyDescriptionError,
    EmptyTypeError,
    ExcessParameterError,
    ExcessRaiseError,
    ExcessVariableError,
    ExcessYieldError,
    GenericSyntaxError,
    IndentError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
    ParameterTypeMismatchError,
    ParameterTypeMissingError,
    ParameterMalformedError,
    ReturnTypeMismatchError,
)
from darglint.utils import (
    ConfigurationContext,
)

from .utils import reindent


class IntegrityCheckerNumpyTestCase(TestCase):

    def setUp(self):
        self.context = ConfigurationContext(
            ignore=[],
            message_template=None,
            style=DocstringStyle.NUMPY,
            strictness=Strictness.FULL_DESCRIPTION,
        )
        self.config = self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def test_missing_parameter(self):
        program = '\n'.join([
            'def cons(x, l):',
            '    """Add an item to the head of the list.',
            '',
            '    Parameters',
            '    ----------',
            '    x',
            '        The item to add to the list.',
            '',
            '    Returns',
            '    -------',
            '    The list with the item attached.',
            '',
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

    def test_doesnt_require_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    Parameters',
            '    ----------',
            '    fn',
            '        A function which takes two items and produces',
            '        one as a result.',
            '    l',
            '        The list to reduce.',
            '',
            '    Returns',
            '    -------',
            '    The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 0,
            [(x.message()) for x in errors],
        )

    def test_runs_other_checks_on_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    Parameters',
            '    ----------',
            '    fn',
            '        A function which takes two items and produces',
            '        one as a result.',
            '    l',
            '        The list to reduce.',
            '    _curr',
            '',
            '    Returns',
            '    -------',
            '    The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors],
        )
        self.assertTrue(
            isinstance(errors[0], EmptyDescriptionError),
            errors[0].__class__.__name__
        )

    def test_empty_type_in_raises_section(self):
        program = '\n'.join([
            'def never():',
            '    """Is never called.',
            '',
            '    Raises',
            '    ------',
            '    AssertionError :',
            '        If it has been called.',
            '',
            '    """',
            '    raise AssertionError()',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors  =checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors],
        )
        self.assertTrue(
            isinstance(errors[0], EmptyTypeError),
            errors[0].__class__.__name__,
        )

    @skip('See Issue #69: https://github.com/terrencepreilly/darglint/issues/69#issuecomment-596273866')  # noqa: E501
    def test_empty_description_error(self):
        program_template = '\n'.join([
            'def f():',
            '    """Has arguments.',
            '    ',
            '    {}',
            '    {}',
            '    {}',
            '',
            '    """',
            '    scream()',
        ])

        for section, item in [('Parameters', 'x')]:
            program = program_template.format(
                section,
                '-' * len(section),
                item,
            )
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            checker = IntegrityChecker(self.config)
            checker.run_checks(function)
            errors = checker.errors
            self.assertTrue(
                len(errors) > 0,
                'EmptyDescriptionError not defined for {}'.format(section),
            )
            self.assertTrue(
                any([
                    isinstance(error, EmptyDescriptionError)
                    for error in errors
                ]),
                'EmptyDescriptionError not defined for {}: {}'.format(
                    section,
                    errors,
                ),
            )

    def test_parameter_types_captured(self):
        program = '\n'.join([
            'class Spectrum:',
            '    @classmethod',
            '    def from_load_name(',
            '        cls,',
            '        load_name: str,',
            '        direc: [str, Path],',
            '        run_num: Optional[int] = None,',
            '        filetype: Optional[str] = None,',
            '        **kwargs',
            '    ):',
            '        """Instantiate the class from a given load name and directory.',
            '',
            '        Parameters',
            '        ----------',
            '        load_name : str',
            '            The load name (one of \'ambient\', \'hot_load\', \'open\' or \'short\').',
            '        direc : Union[str, Path]',
            '            The top-level calibration observation directory.',
            '        run_num : Optional[int]',
            '            The run number to use for the spectra.',
            '        filetype : Optional[str]',
            '            The filetype to look for (acq or h5).',
            '        kwargs :',
            '            All other arguments to :class:`LoadSpectrum`.',
            '',
            '        Returns',
            '        -------',
            '        :class:`LoadSpectrum`.',
            '        """',
            '        return LoadSpectrum()',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker(self.config)
        checker.run_checks(function)
        errors = checker.errors

        self.assertTrue(
            len(errors) == 1,
            'EmptyTypeError not defined among {}'.format(
                '\n'.join(map(lambda x: x.message(2), errors)),
            ),
        )
        self.assertTrue(
            isinstance(errors[0], EmptyTypeError),
            'EmptyTypeError not defined: {}'.format(
                errors,
            ),
        )


class IntegrityCheckerSphinxTestCase(TestCase):

    def setUp(self):
        self.context = ConfigurationContext(
            ignore=[],
            message_template=None,
            style=DocstringStyle.SPHINX,
            strictness=Strictness.FULL_DESCRIPTION,
        )
        self.config = self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

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

    def test_return_incorrectly_has_parameter(self):
        """Make sure that a return with a parameter is parsed correctly."""
        program = '\n'.join([
            'def f():',
            '    """Some fn',
            '    :return x: some value',
            '    """',
            '    return 3',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker(self.config)
        checker.run_checks(function)
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors]
        )

    def test_underspecified_parameter_types(self):
        program = '\n'.join([
            'def f(x: int, y, z: str):',
            '    """Some fn.',
            '',
            '    :param x: The first argument.',
            '    :type x: int',
            '    :param y: The second argument.',
            '    :param z: The third argument.',
            '    :type z: str',
            '',
            '    """',
            '    print(z + str(x * y))',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker(self.config)
        checker.run_checks(function)
        errors = checker.errors
        # It's okay if we allow underspecified types -- so long
        # as we don't incorrectly raise an execption.
        self.assertTrue(
            len(errors) <= 1,
            [(x.message()) for x in errors]
        )
        if errors:
            self.assertTrue(
                isinstance(errors[0], ParameterTypeMissingError),
                'Expected {} to be a ParameterTypeMissingError'.format(
                    errors[0].__class__.__name__,
                ),
            )

    def test_empty_description_error(self):
        program_template = '\n'.join([
            'def f():',
            '    """Makes the thing scream.'
            '    ',
            '    :{}:',
            '    """',
            '    scream()',
        ])

        for section in ['param x', 'return', 'var x',
                        'type x', 'vartype x', 'raises Exception',
                        'yield', 'ytype', 'rtype']:
            program = program_template.format(section)
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            checker = IntegrityChecker(self.config)
            checker.run_checks(function)
            errors = checker.errors
            self.assertTrue(
                len(errors) > 0,
                'EmptyDescriptionError not defined for {}'.format(section),
            )
            self.assertTrue(
                any([
                    isinstance(error, EmptyDescriptionError)
                    for error in errors
                ]),
                'EmptyDescriptionError not defined for {}: {}'.format(
                    section,
                    errors,
                ),
            )

    def test_missing_parameter_types(self):
        program = '\n'.join([
            'def function_with_excess_parameter(extra):',
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

        with ConfigurationContext(
            ignore=[],
            message_template=None,
            style=DocstringStyle.GOOGLE,
            strictness=Strictness.FULL_DESCRIPTION,
            enable=['DAR104']
        ):
            checker = IntegrityChecker()
            checker.run_checks(functions[0])
            errors = checker.errors
            self.assertEqual(len(errors), 1)
            self.assertTrue(isinstance(errors[0], ParameterTypeMissingError))

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

    def test_catch_and_raise(self):
        program = '\n'.join([
            'def false_positive() -> None:',
            '    """summary',
            '',
            '    :raises ValueError: description',
            '    """',
            '    try:',
            '        raise ValueError("233")',
            '    except ValueError as e:',
            '        raise e from None',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker(self.config)
        checker.run_checks(function)
        self.assertEqual(
            len(checker.errors),
            0,
            checker.errors,
        )

    def test_doesnt_require_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    :param fn: A function which takes two items and produces',
            '        one as a result.',
            '    :param l: The list to reduce.',
            '    :return: The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 0,
            [(x.message()) for x in errors],
        )

    def test_runs_other_checks_on_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    :param fn: A function which takes two items and produces',
            '        one as a result.',
            '    :param l: The list to reduce.',
            '    :param _curr:',
            '    :return: The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker(self.config)
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors],
        )
        self.assertTrue(
            isinstance(errors[0], EmptyDescriptionError),
            errors[0].__class__.__name__
        )

class IntegrityCheckerTestCase(TestCase):

    def test_ignore_private_methods(self):
        program = '\n'.join([
            'def function_with_missing_parameter(x):',
            '    """We\'re missing a description of x."""',
            '    print(x / 2)',
            ''
            'def _same_error_but_private_method(x):',
            '    """We\'re missing a description of x."""',
            '    print(x / 2)',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        with ConfigurationContext(
            ignore=[],
            message_template=None,
            style=DocstringStyle.GOOGLE,
            strictness=Strictness.FULL_DESCRIPTION,
            ignore_regex=r'^_(.*)'
        ):
            checker = IntegrityChecker()
            checker.run_checks(functions[0])
            checker.run_checks(functions[1])

            errors = checker.errors
            self.assertEqual(len(errors), 1)

    def test_ignore_style_errors(self):
        program = '\n'.join([
            'class WebsiteChecker:',
            '    def add_to_bloom_filter(self, x):',
            '        """Add the item to the bloom filter.',
            '    ',
            '        Args:',
            '            x: The item to add to the bloom filter.',
            '              Assumed to be hashable.',
            '    ',
            '        """',
            '        self.bloom.update(x)',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        with ConfigurationContext(
            ignore=['DAR003'],
            message_template=None,
            style=DocstringStyle.GOOGLE,
            strictness=Strictness.FULL_DESCRIPTION,
        ):
            checker = IntegrityChecker()
            checker.run_checks(functions[0])
            errors = checker.errors
            self.assertEqual(len(errors), 0)

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

    def test_underspecified_parameter_types(self):
        program = '\n'.join([
            'def f(x: int, y, z: str):',
            '    """Some fn.',
            '',
            '    Args:',
            '        x (int): Some value.',
            '        y: Some value.',
            '        z (str): Some value.',
            '',
            '    """',
            '    print(z + str(x * y))',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker()
        checker.run_checks(function)
        errors = checker.errors
        # It's okay if we allow underspecified types -- so long
        # as we don't incorrectly raise an execption.
        self.assertTrue(
            len(errors) <= 1,
            [(x.message()) for x in errors]
        )
        if errors:
            self.assertTrue(
                isinstance(errors[0], ParameterTypeMissingError),
                'Expected {} to be a ParameterTypeMissingError'.format(
                    errors[0].__class__.__name__,
                ),
            )

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

    def test_malformed_errors_raise_appropriate_warning(self):
        program = '\n'.join([
            'def append_markdown(content):',
            '    """Adds the content to this markdown.',
            '',
            '    Args:',
            '        content (str | list(str)): The content to add.',
            '',
            '    """',
            '    if isinstance(content, str):',
            '        this.contents.append(content)',
            '    elif isinstance(content, list):',
            '        this.content.extend(content)',
            '    else:',
            '        logger.warning("Invalid content type")',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], ParameterMalformedError))

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
            'Expected there to be no errors, but there were {}:\n\t{}'.format(
                len(checker.errors),
                '\n\t'.join([x.general_message for x in checker.errors])
            )
        )

    def test_noqa_after_excess_raises(self):
        program = '\n'.join([
            'def some_function():',
            '    """Raise an error.',
            '',
            '    Raises:',
            '        Exception: In all cases.  # noqa: DAR402',
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
            '    # noqa: DAR401 Exception',
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
            '        x: Will be here eventually.  # noqa: DAR102',
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
            '    # noqa: DAR101',
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
            '    # noqa: DAR201',
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
            '    # noqa: DAR202',
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
            '    # noqa: DAR301',
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
            '    # noqa: DAR302',
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
            '    # noqa: DAR103',
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
            '    # noqa: DAR103 x',
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
            '    # noqa: DAR203',
            '',
            '    """',
            '    x.update({"data": 3})',
            '    return x',
        ])
        self.has_no_errors(program)

    @skip('Fix this!')
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

        # The default is to not raise exceptions.
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertTrue(isinstance(errors[0], GenericSyntaxError))

    def test_error_if_no_colon_in_parameter_line_cyk(self):
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
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertTrue(isinstance(errors[0], IndentError))

    def test_catch_and_raise(self):
        program = '\n'.join([
            'def false_positive() -> None:',
            '    """summary',
            '',
            '    Raises:',
            '        ValueError: description',
            '',
            '    """',
            '    try:',
            '        raise ValueError("233")',
            '    except ValueError as e:',
            '        raise',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        checker = IntegrityChecker()
        checker.run_checks(function)
        self.assertEqual(
            len(checker.errors),
            0,
            checker.errors,
        )

    def test_raises_style_error_if_no_content_after_colon(self):
        program_template = '\n'.join([
            'def hello_world():',
            '    """Tell the person hello.',
            '',
            '    {}:',
            '        {}:',
            '',
            '    """',
            '    person.hello()',
        ])
        for section, item in [
            ('Args', 'name'),
            ('Raises', 'Exception'),
        ]:
            program = program_template.format(section, item)
            tree = ast.parse(program)
            functions = get_function_descriptions(tree)
            checker = IntegrityChecker()
            checker.run_checks(functions[0])
            errors = checker.errors
            self.assertTrue(
                len(errors) > 0,
                'Failed to raise any errors for {}'.format(section),
            )
            self.assertTrue(
                any([
                    isinstance(error, EmptyDescriptionError)
                    for error in errors
                ]),
                'Failed to raise EmptyDescriptionError for {}'.format(section),
            )

    def test_bare_return_doesnt_count_but_doesnt_count_against(self):
        program_template = reindent(r'''
            def f(x):
                """{}"""
                if x == 0:
                    return
                print(1 / x)
        ''')
        without_return = program_template.format(reindent(r'''
            Print the inverse.

            Args:
                x: The value whose inverse we may print.
        '''))
        self.has_no_errors(without_return)
        with_return = program_template.format(reindent(r'''
            Print the inverse.

            Args:
                x: The value whose inverse we may print.

            Returns:
                Nothing.
        '''))
        self.has_no_errors(with_return)



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
        for variant in ['# noqa: *', '# noqa: DAR001', '# noqa']:
            self.has_no_errors(program.format(variant))

    def test_star_args_are_optional(self):
        program = '\n'.join([
            'def collapse_many_logs(*args: typing.List[str]) '
            '-> typing.List[str]:',
            '    """Concatenate an arbitrary number of lists, '
            'with a separator.',
            '',
            '    Args:',
            '        args: Any number of lists of strings.',
            '',
            '    Returns:',
            '        A list of strings made up of the input lists, '
            'skipping empty lists and',
            '        putting a separator between the remainder.',
            '    """',
            '    return []',
        ])
        self.has_no_errors(program)

    def test_empty_type_section(self):
        program = '\n'.join([
            'def foo(bar):',
            '    """Foo.',
            '',
            '    Args:',
            '        bar (): A bar.',
            '    """',
            '    print(bar)',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors]
        )
        self.assertTrue(isinstance(
            errors[0], EmptyTypeError
        ), errors[0].__class__.__name__)

    def test_doesnt_require_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    Args:',
            '        fn: A function which takes two items and produces',
            '            one as a result.',
            '        l: The list to reduce.',
            '',
            '    Returns:',
            '        The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 0,
            [(x.message()) for x in errors],
        )

    def test_runs_other_checks_on_private_arguments(self):
        program = '\n'.join([
            'def reduce(fn, l, _curr=None):',
            '    """Reduce the list with the given function.',
            '',
            '    Args:',
            '        fn: A function which takes two items and produces',
            '            one as a result.',
            '        l: The list to reduce.',
            '        _curr:',
            '',
            '    Returns:',
            '        The final, reduced result of the list.',
            '',
            '    """',
            '    if not l:',
            '        return _curr',
            '    if not _curr:',
            '        return reduce(fn, l[1:], l[0])',
            '    return reduce(fn, l[1:], fn(l[0], _curr))',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors), 1,
            [(x.message()) for x in errors],
        )
        self.assertTrue(
            isinstance(errors[0], EmptyDescriptionError),
            errors[0].__class__.__name__
        )

    def test_assertion_error_allowed(self):
        program = '\n'.join([
            'def assertEven(x):',
            '    """Ensures that the argument is even.',
            '',
            '    Args:',
            '        x: The argument to check.',
            '',
            '    Raises:',
            '        AssertionError: If the argument is odd.',
            '',
            '    """',
            '    assert x % 2 == 0, "Not even!"',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        checker = IntegrityChecker()
        checker.run_checks(functions[0])
        errors = checker.errors
        self.assertEqual(
            len(errors),
            0,
        )

class StrictnessTests(TestCase):

    def setUp(self):
        self.short_google_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.SHORT_DESCRIPTION,
        }
        self.long_google_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.LONG_DESCRIPTION,
        }
        self.full_google_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.FULL_DESCRIPTION,
        }
        self.short_sphinx_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.SPHINX,
            'strictness': Strictness.SHORT_DESCRIPTION,
        }
        self.long_sphinx_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.SPHINX,
            'strictness': Strictness.LONG_DESCRIPTION,
        }
        self.full_sphinx_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.SPHINX,
            'strictness': Strictness.FULL_DESCRIPTION,
        }
        self.two_spaces_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.FULL_DESCRIPTION,
            'indentation': 2,
        }
        self.short_docstring = 'Adds an item to the head of the list.'
        self.long_docstring = '\n'.join([
            'Adds an item to the head of the list',
            '',
            'Not very pythonic.',
        ])
        self.full_docstring = '\n'.join([
            'Adds an item to the head of the list',
            '',
            'Not very pythonic, but oh well.',
            '',
            'Args:',
            '    x: Definitely only the head is required.',
        ])
        self.full_docstring_sphinx = '\n'.join([
            'Adds an item to the head of the list',
            '',
            'Not very pythonic, but oh well.',
            '',
            ':param x: Definitely only the head is required.',
        ])
        self.two_spaces_docstring = '\n'.join([
            'Adds an item to the head of the list',
            '',
            'Not very pythonic, but oh well.',
            '',
            'Args:',
            '  x: Definitely only the head is required.',
            '  l: The list to append to.',
            '',
            'Returns:',
            '  A new list with the item prepended.',
        ])

    def get_function_with(self, docstring):
        program = '\n'.join([
            'def cons(x, l):',
            '    """{}"""'.format(docstring),
            '    return [x] + l',
        ])
        tree = ast.parse(program)
        return get_function_descriptions(tree)[0]

    def assertHasNoErrors(self, config, docstring):
        with ConfigurationContext(**config):
            checker = IntegrityChecker()
            checker.run_checks(self.get_function_with(docstring))
            errors = checker.errors
            self.assertEqual(
                len(errors),
                0,
                [(x.message()) for x in errors]
            )

    def assertHasErrors(self, config, docstring):
        with ConfigurationContext(**config):
            checker = IntegrityChecker()
            checker.run_checks(self.get_function_with(docstring))
            errors = checker.errors
            self.assertTrue(
                len(errors) > 0
            )

    def test_short_google_strictness(self):
        self.assertHasNoErrors(self.short_google_config, self.short_docstring)

    def test_long_google_strictness(self):
        for doc in [
            self.short_docstring,
            self.long_docstring,
        ]:
            self.assertHasNoErrors(self.long_google_config, doc)

    def test_not_google_short_description(self):
        for doc in [
            self.long_docstring,
            self.full_docstring,
        ]:
            self.assertHasErrors(self.short_google_config, doc)

    def test_not_google_long_description(self):
        self.assertHasErrors(self.long_google_config, self.full_docstring)

    def test_google_full_description(self):
        for doc in [
            self.short_docstring,
            self.long_docstring,
            self.full_docstring,
        ]:
            self.assertHasErrors(self.full_google_config, doc)

    def test_short_sphinx(self):
        self.assertHasNoErrors(self.short_sphinx_config, self.short_docstring)
        for doc in [
            self.long_docstring,
            self.full_docstring_sphinx,
        ]:
            self.assertHasErrors(self.short_sphinx_config, doc)

    def test_long_sphinx(self):
        for doc in [
            self.short_docstring,
            self.long_docstring,
        ]:
            self.assertHasNoErrors(self.long_sphinx_config, doc)
        self.assertHasErrors(
            self.long_sphinx_config,
            self.full_docstring_sphinx,
        )

    def test_full_sphinx(self):
        for doc in [
            self.short_docstring,
            self.long_docstring,
            self.full_docstring_sphinx,
        ]:
            self.assertHasErrors(self.full_sphinx_config, doc)

    def test_two_spaces(self):
        self.assertHasNoErrors(
            self.two_spaces_config,
            self.two_spaces_docstring,
        )
