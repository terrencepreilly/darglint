"""This module describes all errors which can be reported by Darglint.

Errors can be anything from being unable to parse a docstring,
to having docstring arguments out of sync with the function/method
definition.

Groups of errors:
    I Interface
    S Style

    100 Args
    200 Returns
    300 Yields
    400 Raises

These errors are based on the errors and warnings from the
pycodestyle package.  Interface, here, describes incorrect or incomplete
documentation.  Style, here, means errors in documentation style.
So, for instance, missing a parameter in the documentation would be
I101.

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

    # A unique human-readable identifier for this type of error.
    # See the description of error code groups above.
    error_code = None

    def __init__(self, function: ast.FunctionDef):
        """Create a new exception with a message and line number.

        Args:
            function: An ast node for the function.

        """
        self.function = function

        # The abstract base class syntax was too verbose for this,
        # and not really justified by the size of the module.
        if (self.message is None
                or self.terse_message is None
                or self.general_message is None
                or self.error_code is None):
            raise NotImplementedError


class MissingParameterError(DarglintError):
    """Describes when a docstring is missing a parameter in the definition."""

    error_code = 'I101'

    def __init__(self, function: ast.FunctionDef, name: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the argument that is missing.

        """
        self.general_message = 'Missing parameter(s) in Docstring'
        self.message = '- {}'.format(name)
        self.terse_message = name
        super(MissingParameterError, self).__init__(function)


class ExcessParameterError(DarglintError):
    """Describes when a docstring contains a parameter not in function."""

    error_code = 'I102'

    def __init__(self, function: ast.FunctionDef, name: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the argument that is excess.

        """
        self.general_message = 'Excess parameter(s) in Docstring'
        self.message = '+ {}'.format(name)
        self.terse_message = name
        super(ExcessParameterError, self).__init__(function)


class ParameterTypeMismatchError(DarglintError):
    """Describes when a docstring parameter type doesn't match function."""

    error_code = 'I103'

    def __init__(self,
                 function: ast.FunctionDef,
                 name: str,
                 expected: str,
                 actual: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the parameter.
            expected: The type defined in the function.
            actual: The type described in the docstring.

        """
        self.general_message = 'Parameter type mismatch'
        self.terse_message = ' ~{}: expected {} but was {}'.format(
            name,
            expected,
            actual,
        )
        self.message = (
            'Parameter type mismatch for "{}": expected {} but was {}'.format(
                name,
                expected,
                actual,
            )
        )
        self.name = name
        self.expected = expected
        self.actual = actual
        super(ParameterTypeMismatchError, self).__init__(function)


class MissingReturnError(DarglintError):
    """Describes when a docstring is missing a return from definition."""

    error_code = 'I201'

    def __init__(self, function: ast.FunctionDef):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.

        """
        self.general_message = 'Missing "Returns" in Docstring'
        self.message = 'Missing "Returns" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(MissingReturnError, self).__init__(function)


class ExcessReturnError(DarglintError):
    """Describes when a docstring has a return not in definition."""

    error_code = 'I202'

    def __init__(self, function: ast.FunctionDef):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.

        """
        self.general_message = 'Excess "Returns" in Docstring'
        self.message = 'Excess "Returns" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(ExcessReturnError, self).__init__(function)


class ReturnTypeMismatchError(DarglintError):
    """Describes when a docstring parameter type doesn't match function."""

    error_code = 'I203'

    def __init__(self,
                 function: ast.FunctionDef,
                 expected: str,
                 actual: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            expected: The type defined in the function.
            actual: The type described in the docstring.

        """
        self.general_message = 'Return type mismatch'
        self.terse_message = ' ~Return: expected {} but was {}'.format(
            expected,
            actual,
        )
        self.message = (
            'Return type mismatch: expected {} but was {}'.format(
                expected,
                actual,
            )
        )
        self.expected = expected
        self.actual = actual
        super(ReturnTypeMismatchError, self).__init__(function)


class MissingYieldError(DarglintError):
    """Describes when a docstring is missing a yield present in definition."""

    error_code = 'I301'

    def __init__(self, function: ast.FunctionDef):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.

        """
        self.general_message = 'Missing "Yields" in Docstring'
        self.message = 'Missing "Yields" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(MissingYieldError, self).__init__(function)


class ExcessYieldError(DarglintError):
    """Describes when a docstring has a yield not in definition."""

    error_code = 'I302'

    def __init__(self, function: ast.FunctionDef):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.

        """
        self.general_message = 'Excess "Yields" in Docstring'
        self.message = 'Excess "Yields" in Docstring'

        # We don't need a terse message, because there is only one
        # instance of this error per function.
        self.terse_message = ''

        super(ExcessYieldError, self).__init__(function)


class MissingRaiseError(DarglintError):
    """Describes when a docstring is missing an exception raised."""

    error_code = 'I401'

    def __init__(self, function: ast.FunctionDef, name: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the exception that is missing.

        """
        self.general_message = 'Missing exception(s) in Raises section'
        self.message = '-r {}'.format(name)
        self.terse_message = name
        self.name = name
        super(MissingRaiseError, self).__init__(function)


class ExcessRaiseError(DarglintError):
    """Describes when docstring describes an exception not explicitly raised.

    This error should not be included by default.  We assume that the user
    knows when an underlying function is likely to raise an error.  Of course,
    we should provide the option, if the user wants to be explicit.  (And
    catch and reraise an exception.)

    """

    error_code = 'I402'

    def __init__(self, function: ast.FunctionDef, name: str):
        """Instantiate the error's message.

        Args:
            function: An ast node for the function.
            name: The name of the exception that is surplus.

        """
        self.general_message = 'Excess exception(s) in Raises section'
        self.message = '-r {}'.format(name)
        self.terse_message = name
        self.name = name
        super(ExcessRaiseError, self).__init__(function)
