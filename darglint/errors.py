"""This module describes all errors which can be reported by Darglint.

Errors can be anything from being unable to parse a docstring,
to having docstring arguments out of sync with the function/method
definition.
"""
import ast


class DarglintError(BaseException):
    """The base error class for any darglint error."""

    # General messages should be general in nature. (They are used
    # at the lowest verbosity setting.)  They should be about
    # the nature of the error, and not about this particular instance.
    # Should not end in any punctuation (and should allow lists of
    # instances -- the terse message -- after it.)
    general_message = None

    # Terse messages should be able to be combined with the general
    # message to give hints as to this particular instance.
    terse_message = None

    # The normal message should describe this instance of the error.
    message = None

    def __init__(self, function: ast.FunctionDef):
        """Create a new exception with a message and line number.

        Args:
            line_number: The line number to display to the user.

        """
        self.function = function
        if (self.message is None
                or self.terse_message is None
                or self.general_message is None):
            raise NotImplementedError


class ExcessReturnError(DarglintError):
    """Describes when a docstring has a return not in definition."""

    def __init__(self, function):
        """Instantiate the error's message."""
        self.general_message = 'Excess "Returns" in Docstring'
        self.message = 'Excess "Returns" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(ExcessReturnError, self).__init__(function)


class MissingReturnError(DarglintError):
    """Describes when a docstring is missing a return from definition."""

    def __init__(self, function):
        """Instantiate the error's message."""
        self.general_message = 'Missing "Returns" in Docstring'
        self.message = 'Missing "Returns" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(MissingReturnError, self).__init__(function)


class ExcessParameterError(DarglintError):
    """Describes when a docstring contains a parameter not in function."""

    def __init__(self, function, name):
        """Instantiate the error's message."""
        self.general_message = 'Excess parameter(s) in Docstring.'
        self.message = '+ {}'.format(name)
        self.terse_message = name
        super(ExcessParameterError, self).__init__(function)


class MissingParameterError(DarglintError):
    """Describes when a docstring is missing a parameter in the definition."""

    def __init__(self, function, name):
        """Instantiate the error's message."""
        self.general_message = 'Missing parameter(s) in Docstring'
        self.message = '- {}'.format(name)
        self.terse_message = name
        super(MissingParameterError, self).__init__(function)
