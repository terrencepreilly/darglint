"""This module describes all errors which can be reported by Darglint.

Errors can be anything from being unable to parse a docstring,
to having docstring arguments out of sync with the function/method
definition.
"""
import ast


class DarglintError(BaseException):
    """The base error class for any darglint error."""

    message = None

    def __init__(self, function: ast.FunctionDef):
        """Create a new exception with a message and line number.

        Args:
            line_number: The line number to display to the user.

        """
        self.function = function
        if self.message is None:
            raise NotImplementedError


class ExcessReturnError(DarglintError):
    """Describes when a docstring has a return not in definition."""

    def __init__(self, function):
        """Instantiate the error's message."""
        self.message = 'Excess Return in Docstring'
        super(ExcessReturnError, self).__init__(function)


class MissingReturnError(DarglintError):
    """Describes when a docstring is missing a return from definition."""

    def __init__(self, function):
        """Instantiate the error's message."""
        self.message = 'Missing Return in Docstring'
        super(MissingReturnError, self).__init__(function)


class ExcessParameterError(DarglintError):
    """Describes when a docstring contains a parameter not in function."""

    def __init__(self, function, name):
        """Instantiate the error's message."""
        self.message = '+ {}'.format(name)
        super(ExcessParameterError, self).__init__(function)


class MissingParameterError(DarglintError):
    """Describes when a docstring is missing a parameter in the definition."""

    def __init__(self, function, name):
        """Instantiate the error's message."""
        self.message = '- {}'.format(name)
        super(MissingParameterError, self).__init__(function)
