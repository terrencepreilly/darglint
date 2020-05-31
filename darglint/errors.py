"""This module describes all errors which can be reported by Darglint.

Errors can be anything from being unable to parse a docstring,
to having docstring arguments out of sync with the function/method
definition.

Groups of errors:

    000 Style
    100 Args
    200 Returns
    300 Yields
    400 Raises
    500 Variables

These errors are based on the errors and warnings from the
pycodestyle package.  Interface, here, describes incorrect or incomplete
documentation.  Style, here, means errors in documentation style.
So, for instance, missing a parameter in the documentation would be
DAR101.

"""
import ast  # noqa: F401
from typing import (  # noqa: F401
    Tuple,
    Union,
)


class DarglintError(BaseException):
    """The base error class for any darglint error."""

    # The shortest error message possible.  Should use abbreviated
    # symbols.  Can be combined with the general message to give
    # a more in-depth message.
    terse_message = None  # type: str

    # General messages should be general in nature. (They are used
    # at the lowest verbosity setting.)  They should be about
    # the nature of the error, and not about this particular instance.
    # Should not end in any punctuation (and should allow lists of
    # instances -- the terse message -- after it.)
    general_message = None  # type: str

    # A unique human-readable identifier for this type of error.
    # See the description of error code groups above.
    error_code = None  # type: str

    # The first and last line numbers where the error occurs.
    line_numbers = None  # type: Tuple[int, int]

    # A description of the error itself.
    description = None  # type: str

    def message(self, verbosity=1):
        # type: (int) -> str
        """Get the message for this error, according to the verbosity.

        Args:
            verbosity: An integer in the set {1,2}, where 1 is a more
                terse message, and 2 includes a general description.

        Raises:
            Exception: If the verbosity level is not recognized.

        Returns:
            An error message.

        """
        if verbosity == 1:
            return '{}'.format(self.terse_message)
        elif verbosity == 2:
            return '{}: {}'.format(
                self.general_message,
                self.terse_message,
            )
        else:
            raise Exception('Unrecognized verbosity setting, {}.'.format(
                verbosity))

    def __init__(self, function, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Tuple[int, int]) -> None
        """Create a new exception with a message and line number.

        Raises:
            NotImplementedError: If the required methods in this
                base class have not been implemented.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.function = function

        if line_numbers:
            self.line_numbers = line_numbers

        # The abstract base class syntax was too verbose for this,
        # and not really justified by the size of the module.
        if (self.terse_message is None
                or self.general_message is None
                or self.error_code is None):
            raise NotImplementedError


class PythonSyntaxError(DarglintError):
    """Describes a syntax error in parsing the python module.."""

    error_code = 'DAR000'
    description = (
        'Failed to parse file due to syntax error.'
    )

    def __init__(self, source):
        # type: (SyntaxError) -> None  # noqa: E501
        """Instantiate the error's message.

        Args:
            source: The syntax error which was raised by ast.

        """
        self.general_message = 'Python syntax error'
        self.terse_message = 's {}'.format(source)
        self.line_numbers = (source.lineno, source.lineno)


class GenericSyntaxError(DarglintError):
    """Describes that something went wrong in parsing the docstring."""

    error_code = 'DAR001'
    description = (
        'The docstring was not parsed correctly due to a syntax error.'
    )

    def __init__(self, function, message, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None  # noqa: E501
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            message: The parser error's message.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Syntax error'
        self.terse_message = 's {}'.format(message)

        super(GenericSyntaxError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class EmptyDescriptionError(DarglintError):
    """Describes when an argument/exception lacks a description."""

    error_code = 'DAR002'
    description = 'An argument/exception lacks a description'

    def __init__(self, function, message, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None  # noqa: E501
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            message: The parser error's message.
            line_numbers: The line numbers where this error occurs.
                Unused.

        """
        self.general_message = 'Empty description'
        self.terse_message = 'e {}'.format(message)

        super(EmptyDescriptionError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class IndentError(DarglintError):
    """Describes when a line is under-indented or over-indented.
    """

    error_code = 'DAR003'
    description = 'A line is under-indented or over-indented.'

    def __init__(self, function, line_numbers=None):
        # type: (ast.FunctionDef, Tuple[int, int]) -> None
        """Instantiate the eror's message.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Incorrect indentation'
        self.terse_message = '~<'

        super(IndentError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessNewlineError(DarglintError):
    """Describes when a docstring has an extra newline where it shouldn't."""

    error_code = 'DAR004'
    description = (
        'The docstring contains an extra newline where it shouldn\'t.'
    )

    def __init__(self, function, line_numbers=None):
        # type: (ast.FunctionDef, Tuple[int, int]) -> None
        self.general_message = 'Excess newline.'
        self.terse_message = '+>'
        super(ExcessNewlineError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class EmptyTypeError(DarglintError):
    """Describes when an item has parentheses, but no type."""

    error_code = 'DAR005'
    description = (
        'The item contains a type section (parentheses), but no type.'
    )

    def __init__(self, function, message, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None  # noqa: E501
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            message: The parser error's message.
            line_numbers: The line numbers where this error occurs.
                Unused.

        """
        self.general_message = 'Empty type'
        self.terse_message = 'e {}'.format(message)

        super(EmptyTypeError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class MissingParameterError(DarglintError):
    """Describes when a docstring is missing a parameter in the definition."""

    error_code = 'DAR101'
    description = 'The docstring is missing a parameter in the definition.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the argument that is missing.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Missing parameter(s) in Docstring'
        self.terse_message = '- {}'.format(name)
        super(MissingParameterError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessParameterError(DarglintError):
    """Describes when a docstring contains a parameter not in function."""

    error_code = 'DAR102'
    description = 'The docstring contains a parameter not in function.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the argument that is excess.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Excess parameter(s) in Docstring'
        self.terse_message = '+ {}'.format(name)
        super(ExcessParameterError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ParameterTypeMismatchError(DarglintError):
    """Describes when a docstring parameter type doesn't match function."""

    error_code = 'DAR103'
    description = 'The docstring parameter type doesn\'t match function.'

    def __init__(self, function, name, expected, actual, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, str, str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the parameter.
            expected: The type defined in the function.
            actual: The type described in the docstring.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Parameter type mismatch'
        self.terse_message = ' ~{}: expected {} but was {}'.format(
            name,
            expected,
            actual,
        )
        self.name = name
        self.expected = expected
        self.actual = actual
        super(ParameterTypeMismatchError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ParameterTypeMissingError(DarglintError):
    """Describes when a argument definition has no type specified"""

    error_code = 'DAR104'
    description = 'The docstring parameter type is not given.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the parameter.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Parameter type missing'
        self.terse_message = ' ~{}: type was not specified'.format(
            name
        )
        self.name = name
        super(ParameterTypeMissingError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ParameterMalformedError(DarglintError):
    """Describes when an argument type is malformed."""

    error_code = 'DAR105'
    description = (
        'The docstring parameter type is malformed. '
        'Expected parameter type to match syntax from PEP484. '
        'If your parameter contains parentheses, you may want '
        'to switch them to brackets.  E.g. `Union[str, int]`.'
    )

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        self.general_message = 'Parameter type malformed.'
        self.terse_message = ' #{}: type malformed'.format(
            name
        )
        self.name = name
        super(ParameterMalformedError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class MissingReturnError(DarglintError):
    """Describes when a docstring is missing a return from definition."""

    error_code = 'DAR201'
    description = 'The docstring is missing a return from definition.'

    def __init__(self, function, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Missing "Returns" in Docstring'
        self.terse_message = '- return'

        super(MissingReturnError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessReturnError(DarglintError):
    """Describes when a docstring has a return not in definition."""

    error_code = 'DAR202'
    description = 'The docstring has a return not in definition.'

    def __init__(self, function, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Excess "Returns" in Docstring'
        self.terse_message = '+ return'

        super(ExcessReturnError, self).__init__(
            function,
            line_numbers=line_numbers,
        )

class ReturnTypeMismatchError(DarglintError):
    """Describes when a docstring parameter type doesn't match function."""

    error_code = 'DAR203'
    description = 'The docstring parameter type doesn\'t match function.'

    def __init__(self, function, expected, actual, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            expected: The type defined in the function.
            actual: The type described in the docstring.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Return type mismatch'
        self.terse_message = ' ~Return: expected {} but was {}'.format(
            expected,
            actual,
        )
        self.expected = expected
        self.actual = actual
        super(ReturnTypeMismatchError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class MissingYieldError(DarglintError):
    """Describes when a docstring is missing a yield present in definition."""

    error_code = 'DAR301'
    description = 'The docstring is missing a yield present in definition.'

    def __init__(self, function, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Missing "Yields" in Docstring'
        self.terse_message = '- yield'

        super(MissingYieldError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessYieldError(DarglintError):
    """Describes when a docstring has a yield not in definition."""

    error_code = 'DAR302'
    description = 'The docstring has a yield not in definition.'

    def __init__(self, function, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Excess "Yields" in Docstring'
        self.terse_message = '+ yield'

        super(ExcessYieldError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class MissingRaiseError(DarglintError):
    """Describes when a docstring is missing an exception raised."""

    error_code = 'DAR401'
    description = 'The docstring is missing an exception raised.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the exception that is missing.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Missing exception(s) in Raises section'
        self.terse_message = '-r {}'.format(name)
        self.name = name
        super(MissingRaiseError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessRaiseError(DarglintError):
    """Describes when a docstring describes an exception not explicitly raised.

    This error should not be included by default.  We assume that the user
    knows when an underlying function is likely to raise an error.  Of course,
    we should provide the option, if the user wants to be explicit.  (And
    catch and reraise an exception.)

    """

    error_code = 'DAR402'
    description = 'The docstring describes an exception not explicitly raised.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the exception that is surplus.
            line_numbers: The line numbers where this error occurs.

        """
        self.general_message = 'Excess exception(s) in Raises section'
        self.terse_message = '+r {}'.format(name)
        self.name = name
        super(ExcessRaiseError, self).__init__(
            function,
            line_numbers=line_numbers,
        )


class ExcessVariableError(DarglintError):
    """Describes when a docstring describes a variable which is not defined."""

    error_code = 'DAR501'
    description = 'The docstring describes a variable which is not defined.'

    def __init__(self, function, name, line_numbers=None):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], str, Tuple[int, int]) -> None
        """Instantiate the error's message.

        Args:
            function: The ast node for the function.
            name: The name of the variable which is in excess.
            line_numbers: The first and last line numbers where this
                error occurs.

        """
        self.general_message = 'Excess variable description.'
        self.terse_message = '+v {}'.format(name)
        self.name = name
        super(ExcessVariableError, self).__init__(
            function,
            line_numbers=line_numbers,
        )
