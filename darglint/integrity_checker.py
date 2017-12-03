"""Defines IntegrityChecker."""

from typing import (
    List,
    Set,
)

from .function_description import (
    FunctionDescription,
)
from .lex import lex
from .parse import (
    Docstring,
    ParserException,
)
from .errors import (
    DarglintError,
    ExcessParameterError,
    ExcessRaiseError,
    ExcessReturnError,
    ExcessYieldError,
    GenericSyntaxError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
    ParameterTypeMismatchError,
    ReturnTypeMismatchError,
)
from .error_report import (
    ErrorReport,
)
from .config import Configuration


class IntegrityChecker(object):
    """Checks the integrity of the docstring compared to the definition."""

    def __init__(self,
                 config: Configuration = Configuration(ignore=[]),
                 raise_errors: bool = False) -> None:
        """Create a new checker for the given function and docstring.

        Args:
            config: The configuration object for this checker.  Will
                determine which errors to show, etc.
            raise_errors: If true, we will allow ParserExceptions to
                propagate, crashing darglint.  This is mostly useful
                for development.

        """
        self.function = None  # type: FunctionDescription
        self.errors = list()  # type: List[DarglintError]
        self._sorted = True
        self.config = config
        self.docstring = None  # type: Docstring
        self.raise_errors = raise_errors

    def run_checks(self, function: FunctionDescription):
        """Run checks on the given function.

        Args:
            function: A function whose docstring we are verifying.

        """
        self.function = function
        if function.docstring is not None:
            try:
                self.docstring = Docstring(lex(function.docstring))
                self._check_parameters()
                self._check_parameter_types()
                self._check_return()
                self._check_return_type()
                self._check_yield()
                self._check_raises()
                self._sorted = False
            except ParserException as exception:
                if self.raise_errors:
                    raise
                self.errors.append(
                    GenericSyntaxError(
                        self.function.function,
                        message=str(exception),
                    ),
                )

    def _check_parameter_types(self):
        error_code = ParameterTypeMismatchError.error_code
        if self._ignore_error(ParameterTypeMismatchError):
            return
#        is_global = noqa_exists and self.docstring.noqa[error_code] is None
#        if noqa_exists and is_global:
#            return

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
            noqa_exists = error_code in self.docstring.noqa
            name_has_noqa = noqa_exists and name in self.docstring.noqa[
                error_code]
            if not (expected == actual or name_has_noqa):
                self.errors.append(
                    ParameterTypeMismatchError(
                        self.function.function,
                        name=name,
                        expected=expected,
                        actual=actual,
                    )
                )

    def _check_return_type(self):
        error_code = ReturnTypeMismatchError.error_code

        if self._ignore_error(ReturnTypeMismatchError):
            return
#         if error_code in self.docstring.noqa:
#             return

        fun_type = self.function.return_type
        doc_type = self.docstring.return_type
        if fun_type is not None and doc_type is not None:
            if fun_type != doc_type:
                self.errors.append(
                    ReturnTypeMismatchError(
                        self.function.function,
                        expected=fun_type,
                        actual=doc_type,
                    ),
                )

    def _check_yield(self):
        doc_yield = len(self.docstring.yields_description) > 0
        fun_yield = self.function.has_yield
        ignore_missing = self._ignore_error(MissingYieldError)
        ignore_excess = self._ignore_error(ExcessYieldError)
#        ignore_missing = MissingYieldError.error_code in self.docstring.noqa
#        ignore_excess = ExcessYieldError.error_code in self.docstring.noqa
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
        ignore_missing = self._ignore_error(MissingReturnError)
        ignore_excess = self._ignore_error(ExcessReturnError)
#        ignore_missing = MissingReturnError.error_code in self.docstring.noqa
#        ignore_excess = ExcessReturnError.error_code in self.docstring.noqa
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

    def _ignore_error(self, error: DarglintError) -> bool:
        """Return true if we should ignore this error.

        Args:
            error: The error we might be ignoring.

        Returns:
            True if we should ignore all instances of this error,
            otherwise false.

        """
        error_code = error.error_code
        if error_code in self.config.ignore:
            return True
        inline_error = error_code in self.docstring.noqa
        if inline_error and self.docstring.noqa[error_code] is None:
            return True
        return False

    def _remove_ignored(self, missing, error) -> Set:
        """Remove ignored from missing.

        Args:
            missing: A set of missing items.
            error: The error being checked.

        Returns:
            A set of missing items without those to be ignored.

        """
        error_code = error.error_code

        # Ignore globally
        if self._ignore_error(error):
            return set()

        # There are no noqa statements
        inline_ignore = error_code in self.docstring.noqa
        if not inline_ignore:
            return missing

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

    def get_error_report(self, verbosity: int, filename: str) -> str:
        """Return a string representation of the errors.

        Args:
            verbosity: The level of verbosity.  Should be an integer
                in the range [1,3].
            filename: The filename of where the error occurred.

        Returns:
            A string representation of the errors.

        """
        return str(ErrorReport(
            errors=self.errors,
            filename=filename,
            verbosity=verbosity,
        ))
