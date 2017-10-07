"""Defines IntegrityChecker."""

from .darglint import (
    FunctionDescription,
)
from .lex import lex
from .parse import (
    parse_arguments,
    parse_return,
    parse_yield,
)
from .errors import (
    ExcessParameterError,
    ExcessReturnError,
    ExcessYieldError,
    MissingParameterError,
    MissingReturnError,
    MissingYieldError,
)
from .error_report import (
    LowVerbosityErrorReport,
    MidVerbosityErrorReport,
    HighVerbosityErrorReport,
)


class IntegrityChecker(object):
    """Checks the integrity of the docstring compared to the definition."""

    def __init__(self):
        """Create a new checker for the given function and docstring."""
        self.function = None  # type: FunctionDescription
        self.errors = list()  # type: List[DarglintError]
        self._sorted = True

    def run_checks(self, function: FunctionDescription):
        """Run checks on the given function.

        Args:
            function: A function whose docstring we are verifying.

        """
        self.function = function
        self._check_parameters()
        self._check_return()
        self._check_yield()
        self._sorted = False

    def _check_yield(self):
        docstring = self.function.docstring

        if docstring is None:
            return

        doc_yield = len(parse_yield(lex(docstring))) > 0
        fun_yield = self.function.has_yield
        if fun_yield and not doc_yield:
            self.errors.append(
                MissingYieldError(self.function.function)
            )
        elif doc_yield and not fun_yield:
            self.errors.append(
                ExcessYieldError(self.function.function)
            )

    def _check_return(self):
        docstring = self.function.docstring

        # Only check if the docstring is present.
        if docstring is None:
            return

        doc_return = len(parse_return(lex(docstring))) > 0
        fun_return = self.function.has_return
        if fun_return and not doc_return:
            self.errors.append(
                MissingReturnError(self.function.function)
            )
        elif doc_return and not fun_return:
            self.errors.append(
                ExcessReturnError(self.function.function)
            )

    def _check_parameters(self):
        docstring = self.function.docstring

        # Only check if the docstring is present.
        if docstring is None:
            return

        docstring_arguments = set(parse_arguments(lex(docstring)))
        actual_arguments = set(self.function.argument_names)
        missing_in_doc = actual_arguments - docstring_arguments
        for missing in missing_in_doc:
            self.errors.append(
                MissingParameterError(self.function.function, missing)
            )
        missing_in_function = docstring_arguments - actual_arguments
        for missing in missing_in_function:
            self.errors.append(
                ExcessParameterError(self.function.function, missing)
            )

    def _sort(self):
        if not self._sorted:
            self.errors.sort(key=lambda x: x.function.lineno)
            self._sorted = True

    def get_error_report(self, verbosity: int) -> str:
        """Return a string representation of the errors.

        Args:
            verbosity:
                The level of verbosity.  Should be an integer
                in the range [1,3].

        Returns:
            A string representation of the errors.

        """
        error_report = None
        if verbosity <= 1:
            error_report = LowVerbosityErrorReport(self.errors)
        elif verbosity == 2:
            error_report = MidVerbosityErrorReport(self.errors)
        else:
            error_report = HighVerbosityErrorReport(self.errors)
        return str(error_report)
