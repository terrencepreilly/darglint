"""This module describes all errors which can be reported by Darglint.

Errors can be anything from being unable to parse a docstring,
to having docstring arguments out of sync with the function/method
definition.
"""


class DarglintError(BaseException):
    """The base error class for any darglint error."""

    message = None

    def __init__(self, line_number):
        """Create a new exception with a message and line number.

        Args:
            line_number: The line number to display to the user.

        """
        self.line_number = line_number
        if self.message is None:
            raise NotImplementedError


class ExcessReturnError(DarglintError):

    pass


class MissingReturnError(DarglintError):
    """Describes when a docstring is missing a return from definition."""

    pass


class ExcessParameterError(DarglintError):
    """Describes when a docstring contains a parameter not in function."""

    pass


class MissingParameterError(DarglintError):
    """Describes when a docstring is missing a parameter in the definition."""

    pass
