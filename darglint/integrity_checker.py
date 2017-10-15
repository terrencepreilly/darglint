"""Defines IntegrityChecker."""

from .darglint import (
    FunctionDescription,
)
from .lex import lex
from .parse import (
    Docstring,
)
from .errors import (
    ExcessParameterError,
    ExcessRaiseError,
    ExcessReturnError,
    ExcessYieldError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
    ParameterTypeMismatchError,
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
        if function.docstring is not None:
            self.docstring = Docstring(lex(function.docstring))
            self._check_parameters()
            self._check_parameter_types()
            self._check_return()
            self._check_yield()
            self._check_raises()
            self._sorted = False

    def _check_parameter_types(self):
        doc_arg_types = list()
        for name in self.function.argument_names:
            if name not in self.docstring.argument_types:
                doc_arg_types.append(None)
            else:
                doc_arg_types.append(self.docstring.argument_types[name])
        for name, expected, actual in zip(
                self.function.argument_names,
                self.function.argument_types,
                doc_arg_types,
        ):
            if expected is None or actual is None:
                continue
            if expected != actual:
                self.errors.append(
                    ParameterTypeMismatchError(
                        self.function.function,
                        name=name,
                        expected=expected,
                        actual=actual,
                    )
                )

    def _check_yield(self):
        doc_yield = len(self.docstring.yields_description) > 0
        fun_yield = self.function.has_yield
        ignore_missing = MissingYieldError.error_code in self.docstring.noqa
        ignore_excess = ExcessYieldError.error_code in self.docstring.noqa
        if fun_yield and not doc_yield and not ignore_missing:
            self.errors.append(
                MissingYieldError(self.function.function)
            )
        elif doc_yield and not fun_yield and not ignore_excess:
            self.errors.append(
                ExcessYieldError(self.function.function)
            )

    def _check_return(self):
        doc_return = len(self.docstring.returns_description) > 0
        fun_return = self.function.has_return
        ignore_missing = MissingReturnError.error_code in self.docstring.noqa
        ignore_excess = ExcessReturnError.error_code in self.docstring.noqa
        if fun_return and not doc_return and not ignore_missing:
            self.errors.append(
                MissingReturnError(self.function.function)
            )
        elif doc_return and not fun_return and not ignore_excess:
            self.errors.append(
                ExcessReturnError(self.function.function)
            )

    def _check_parameters(self):
        docstring_arguments = set(self.docstring.arguments_descriptions.keys())
        actual_arguments = set(self.function.argument_names)
        missing_in_doc = actual_arguments - docstring_arguments
        missing_in_doc = self._remove_ignored(
            missing_in_doc,
            MissingParameterError,
        )
        for missing in missing_in_doc:
            self.errors.append(
                MissingParameterError(self.function.function, missing)
            )

        missing_in_function = docstring_arguments - actual_arguments
        missing_in_function = self._remove_ignored(
            missing_in_function,
            ExcessParameterError,
        )
        for missing in missing_in_function:
            self.errors.append(
                ExcessParameterError(self.function.function, missing)
            )

    def _remove_ignored(self, missing, error):
        """Remove ignored from missing.

        Args:
            missing: A set of missing items.
            error: The error being checked.

        Returns:
            A set of missing items without those to be ignored.

        """
        error_code = error.error_code

        # There are no noqa statements
        if error_code not in self.docstring.noqa:
            return missing

        # We are to ignore all of this type.
        if self.docstring.noqa[error_code] is None:
            return set()

        # We are to ignore specific instances.
        return missing - set(self.docstring.noqa[error_code])

    def _check_raises(self):
        docstring_raises = set(self.docstring.raises_descriptions.keys())
        actual_raises = self.function.raises
        missing_in_doc = actual_raises - docstring_raises

        missing_in_doc = self._remove_ignored(
            missing_in_doc,
            MissingRaiseError,
        )

        for missing in missing_in_doc:
            self.errors.append(
                MissingRaiseError(self.function.function, missing)
            )

        # TODO: Disable by default.
        #
        # Should we even include this?  It seems like the user
        # would know if this function would be likely to raise
        # a certain exception from underlying calls.
        #
        missing_in_function = docstring_raises - actual_raises
        missing_in_function = self._remove_ignored(
            missing_in_function,
            ExcessRaiseError,
        )
        for missing in missing_in_function:
            self.errors.append(
                ExcessRaiseError(self.function.function, missing)
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
