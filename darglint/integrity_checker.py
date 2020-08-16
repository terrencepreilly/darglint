"""Defines IntegrityChecker."""

import re
import concurrent.futures
from typing import (  # noqa: F401
    Any,
    List,
    Set,
    Optional,
)

from .function_description import (  # noqa: F401
    FunctionDescription,
)
from .docstring.base import (  # noqa: F401
    BaseDocstring,
    DocstringStyle,
)
from .docstring.base import (
    Sections,
)
from .docstring.docstring import (
    Docstring,
)
from .errors import (  # noqa: F401
    DarglintError,
    ExcessParameterError,
    ExcessRaiseError,
    ExcessReturnError,
    ExcessVariableError,
    ExcessYieldError,
    MissingParameterError,
    MissingRaiseError,
    MissingReturnError,
    MissingYieldError,
    ParameterTypeMismatchError,
    ParameterTypeMissingError,
    ReturnTypeMismatchError,
)
from .error_report import (
    ErrorReport,
)
from .config import (
    get_config,
    Strictness,
)


SYNTAX_NOQA = re.compile(r'#\s*noqa:\sS001')
EXPLICIT_GLOBAL_NOQA = re.compile(r'#\s*noqa:\s*\*')
BARE_NOQA = re.compile(r'#\s*noqa([^:]|$)')


class IntegrityChecker(object):
    """Checks the integrity of the docstring compared to the definition."""

    def __init__(self, raise_errors=False):
        # type: (bool) -> None
        """Create a new checker for the given function and docstring.

        Args:
            raise_errors: If true, we will allow ParserExceptions to
                propagate, crashing darglint.  This is mostly useful
                for development.

        """
        self.errors = list()  # type: List[DarglintError]
        self._sorted = True
        self.config = get_config()
        self.raise_errors = raise_errors

        # TODO: Move max workers into a configuration option.
        # A thread pool for handling checks.  Tasks are added to the
        # pool when `schedule` is executed, if it has a docstring.
        # The pool is collected when `get_error_report_string` is called.
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def schedule(self, function):
        # type: (FunctionDescription) -> None
        if self._skip_checks(function):
            return

        self.executor.submit(self.run_checks, function)

    def run_checks(self, function):
        # type: (FunctionDescription) -> None
        """Run checks on the given function.

        Args:
            function: A function whose docstring we are verifying.

        Raises:
            Exception: If the docstring format isn't supported.

        """
        if self._skip_checks(function):
            return

        if self.config.style == DocstringStyle.GOOGLE:
            docstring = Docstring.from_google(
                function.docstring,
            )
        elif self.config.style == DocstringStyle.SPHINX:
            docstring = Docstring.from_sphinx(
                function.docstring,
            )
            self._check_variables(docstring, function)
        elif self.config.style == DocstringStyle.NUMPY:
            docstring = Docstring.from_numpy(
                function.docstring,
            )
        else:
            raise Exception('Unsupported docstring format.')
        if self.config.strictness != Strictness.FULL_DESCRIPTION:
            if docstring.satisfies_strictness(self.config.strictness):
                return
        if docstring.ignore_all:
            return
        self._check_parameters(docstring, function)
        self._check_parameter_types(docstring, function)
        self._check_parameter_types_missing(docstring, function)
        self._check_return(docstring, function)
        self._check_return_type(docstring, function)
        self._check_yield(docstring, function)
        self._check_raises(docstring, function)
        self._check_style(docstring, function)
        self._sorted = False

    def _skip_checks(self, function):
        # type: (FunctionDescription) -> bool
        no_docsting = function.docstring is None
        skip_by_regex = (
            self.config.ignore_regex and
            re.match(self.config.ignore_regex, function.name)
        )

        return bool(no_docsting or skip_by_regex)

    def _check_parameter_types(self, docstring, function):
        # type: (FunctionDescription) -> None
        error_code = ParameterTypeMismatchError.error_code
        if self._ignore_error(docstring, ParameterTypeMismatchError):
            return

        argument_types = dict(
            zip(docstring.get_items(Sections.ARGUMENTS_SECTION) or [],
                docstring.get_types(Sections.ARGUMENTS_SECTION) or [])
        )
        doc_arg_types = list()  # type: List[Optional[str]]
        for name in function.argument_names:
            if name not in argument_types:
                doc_arg_types.append(None)
            else:
                doc_arg_types.append(argument_types[name])
        noqa_lookup = docstring.get_noqas()
        for name, expected, actual in zip(
                function.argument_names,
                function.argument_types,
                doc_arg_types,
        ):
            if expected is None or actual is None:
                continue
            noqa_exists = error_code in noqa_lookup
            name_has_noqa = noqa_exists and name in noqa_lookup[error_code]
            if not (expected == actual or name_has_noqa):
                default_line_numbers = docstring.get_line_numbers(
                    'arguments-section'
                )
                line_numbers = docstring.get_line_numbers_for_value(
                    'ident',
                    name,
                ) or default_line_numbers
                self.errors.append(
                    ParameterTypeMismatchError(
                        function.function,
                        name=name,
                        expected=expected,
                        actual=actual,
                        line_numbers=line_numbers,
                    )
                )

    def _check_parameter_types_missing(self, docstring, function):
        # type: (FunctionDescription) -> None
        error_code = ParameterTypeMissingError.error_code
        if self._ignore_error(docstring, ParameterTypeMissingError):
            return

        argument_types = dict(
            zip(docstring.get_items(Sections.ARGUMENTS_SECTION) or [],
                docstring.get_types(Sections.ARGUMENTS_SECTION) or [])
        )

        noqa_lookup = docstring.get_noqas()
        noqa_exists = error_code in noqa_lookup

        for name, argument_type in argument_types.items():
            name_has_no_qa = noqa_exists and name in noqa_lookup[error_code]

            if argument_type is None and not name_has_no_qa:
                default_line_numbers = docstring.get_line_numbers(
                    'arguments-section'
                )
                line_numbers = docstring.get_line_numbers_for_value(
                    'ident',
                    name,
                ) or default_line_numbers
                self.errors.append(
                    ParameterTypeMissingError(
                        function.function,
                        name=name,
                        line_numbers=line_numbers,
                    )
                )

    def _check_return_type(self, docstring, function):
        # type: (FunctionDescription) -> None
        if self._ignore_error(docstring, ReturnTypeMismatchError):
            return

        fun_type = function.return_type
        doc_type = docstring.get_types(Sections.RETURNS_SECTION)
        if not doc_type or isinstance(doc_type, list):
            doc_type = None
        if fun_type is not None and doc_type is not None:
            if fun_type != doc_type:
                line_numbers = docstring.get_line_numbers(
                    'returns-section',
                )
                self.errors.append(
                    ReturnTypeMismatchError(
                        function.function,
                        expected=fun_type,
                        actual=doc_type,
                        line_numbers=line_numbers,
                    ),
                )

    def _check_yield(self, docstring, function):
        # type: (FunctionDescription) -> None
        doc_yield = docstring.get_section(Sections.YIELDS_SECTION)
        fun_yield = function.has_yield
        ignore_missing = self._ignore_error(docstring, MissingYieldError)
        ignore_excess = self._ignore_error(docstring, ExcessYieldError)
        if fun_yield and not doc_yield and not ignore_missing:
            self.errors.append(
                MissingYieldError(function.function)
            )
        elif doc_yield and not fun_yield and not ignore_excess:
            line_numbers = docstring.get_line_numbers(
                'yields-section',
            )
            self.errors.append(
                ExcessYieldError(
                    function.function,
                    line_numbers=line_numbers,
                )
            )

    def _check_return(self, docstring, function):
        # type: (FunctionDescription) -> None
        doc_return = docstring.get_section(Sections.RETURNS_SECTION)
        fun_return = function.has_return
        ignore_missing = self._ignore_error(docstring, MissingReturnError)
        ignore_excess = self._ignore_error(docstring, ExcessReturnError)
        if fun_return and not doc_return and not ignore_missing:
            self.errors.append(
                MissingReturnError(function.function)
            )
        elif doc_return and not fun_return and not ignore_excess:
            line_numbers = docstring.get_line_numbers(
                'returns-section',
            )
            self.errors.append(
                ExcessReturnError(
                    function.function,
                    line_numbers=line_numbers,
                )
            )

    def _check_parameters(self, docstring, function):
        # type: (FunctionDescription) -> None
        docstring_arguments = set(docstring.get_items(
            Sections.ARGUMENTS_SECTION
        ) or [])
        actual_arguments = set(function.argument_names)
        missing_in_doc = actual_arguments - docstring_arguments
        missing_in_doc = self._remove_ignored(
            docstring,
            missing_in_doc,
            MissingParameterError,
        )

        # Get a default line number.
        default_line_numbers = docstring.get_line_numbers(
            'arguments-section'
        )

        for missing in missing_in_doc:
            # See if the documented argument begins with one
            # or two asterisks.
            if (
                (missing.startswith('**')
                    and missing[2:] in docstring_arguments)
                or (missing.startswith('*')
                    and missing[1:] in docstring_arguments)
            ):
                continue

            # Don't require private arguments.
            if missing.startswith('_'):
                continue

            # We use the default line numbers because a missing
            # parameter, by definition, will not have line numbers.
            self.errors.append(
                MissingParameterError(
                    function.function,
                    missing,
                    line_numbers=default_line_numbers
                )
            )

        missing_in_function = docstring_arguments - actual_arguments
        missing_in_function = self._remove_ignored(
            docstring,
            missing_in_function,
            ExcessParameterError,
        )
        for missing in missing_in_function:
            # If the actual argument begins with asterisk(s),
            # then check to make sure the unasterisked version
            # is not missing.
            if (
                '*' + missing in actual_arguments or
                '**' + missing in actual_arguments
            ):
                continue
            line_numbers = docstring.get_line_numbers_for_value(
                'arguments-section',
                missing,
            ) or default_line_numbers
            self.errors.append(
                ExcessParameterError(
                    function.function,
                    missing,
                    line_numbers=line_numbers,
                )
            )

    def _check_variables(self, docstring, function):
        # type: (FunctionDescription) -> None
        described_variables = set(
            docstring.get_items(Sections.VARIABLES_SECTION) or []
        )  # type: Set[str]
        actual_variables = set(function.variables)
        excess_in_doc = described_variables - actual_variables

        # Get a default line number.
        default_line_numbers = docstring.get_line_numbers(
            'variables-section',
        )

        for excess in excess_in_doc:
            line_numbers = docstring.get_line_numbers_for_value(
                'variables-section',
                excess,
            ) or default_line_numbers
            self.errors.append(
                ExcessVariableError(
                    function.function,
                    excess,
                    line_numbers=line_numbers,
                )
            )

    def _ignore_error(self, docstring, error):
        # type: (Any) -> bool
        """Return true if we should ignore this error.

        Args:
            docstring: The docstring we are reporting on.
            error: The error we might be ignoring.

        Returns:
            True if we should ignore all instances of this error,
            otherwise false.

        """
        error_code = error.error_code
        if error_code in self.config.errors_to_ignore:
            return True
        noqa_lookup = docstring.get_noqas()
        inline_error = error_code in noqa_lookup
        if inline_error and not noqa_lookup[error_code]:
            return True
        return False

    def _remove_ignored(self, docstring, missing, error):
        # type: (Set[str], Any) -> Set[str]
        """Remove ignored from missing.

        Args:
            docstring: The docstring we are reporting on.
            missing: A set of missing items.
            error: The error being checked.

        Returns:
            A set of missing items without those to be ignored.

        """
        error_code = error.error_code

        # Ignore globally
        if self._ignore_error(docstring, error):
            return set()

        # There are no noqa statements
        noqa_lookup = docstring.get_noqas()
        inline_ignore = error_code in noqa_lookup
        if not inline_ignore:
            return missing

        # We are to ignore specific instances.
        return missing - set(noqa_lookup[error_code])

    def _check_style(self, docstring, function):
        # type: (FunctionDescription) -> None
        for StyleError, line_numbers in docstring.get_style_errors():
            if self._ignore_error(docstring, StyleError):
                continue
            self.errors.append(StyleError(
                function.function,
                line_numbers,
            ))

    def _check_raises(self, docstring, function):
        # type: (FunctionDescription) -> None
        exception_types = docstring.get_items(Sections.RAISES_SECTION)
        docstring_raises = set(exception_types or [])
        actual_raises = function.raises
        missing_in_doc = actual_raises - docstring_raises

        missing_in_doc = self._remove_ignored(
            docstring,
            missing_in_doc,
            MissingRaiseError,
        )

        for missing in missing_in_doc:
            self.errors.append(
                MissingRaiseError(function.function, missing)
            )

        # TODO: Disable by default.
        #
        # Should we even include this?  It seems like the user
        # would know if this function would be likely to raise
        # a certain exception from underlying calls.
        #
        missing_in_function = docstring_raises - actual_raises
        missing_in_function = self._remove_ignored(
            docstring,
            missing_in_function,
            ExcessRaiseError,
        )

        # Remove AssertionError if there is an assert.
        if 'AssertionError' in missing_in_function:
            if function.raises_assert:
                missing_in_function.remove('AssertionError')

        default_line_numbers = docstring.get_line_numbers(
            'raises-section',
        )
        for missing in missing_in_function:
            line_numbers = docstring.get_line_numbers_for_value(
                'raises-section',
                missing,
            ) or default_line_numbers
            self.errors.append(
                ExcessRaiseError(
                    function.function,
                    missing,
                    line_numbers=line_numbers,
                )
            )

    def _sort(self):
        # type: () -> None
        if not self._sorted:
            self.errors.sort(key=lambda x: x.function.lineno)
            self._sorted = True

    def get_error_report(self, verbosity, filename, message_template=None):
        # type: (int, str, str) -> ErrorReport
        self.executor.shutdown()
        return ErrorReport(
            errors=self.errors,
            filename=filename,
            verbosity=verbosity,
            message_template=message_template or self.config.message_template,
        )

    def get_error_report_string(self,
                                verbosity,
                                filename,
                                message_template=None):
        # type: (int, str, str) -> str
        """Return a string representation of the errors.

        Args:
            verbosity: The level of verbosity.  Should be an integer
                in the range [1,3].
            filename: The filename of where the error occurred.
            message_template: A python format string for describing
                how the error reports should look to the user.

        Returns:
            A string representation of the errors.

        """
        return str(self.get_error_report(
            verbosity, filename, message_template
        ))
