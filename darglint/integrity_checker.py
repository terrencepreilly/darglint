"""Defines IntegrityChecker."""

import re
from typing import (  # noqa: F401
    Any,
    List,
    Set,
    Optional,
)

from .function_description import (  # noqa: F401
    FunctionDescription,
)
from .parse.common import (
    ParserException,
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
from .node import (
    NodeType,
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
    ReturnTypeMismatchError,
    DefinitionNotStartingWithCapitalError,
    DefinitionNotEndingWithPeriodError,
)
from .error_report import (
    ErrorReport,
)
from .config import (
    Configuration,
    Strictness,
)


SYNTAX_NOQA = re.compile(r'#\s*noqa:\sS001')
EXPLICIT_GLOBAL_NOQA = re.compile(r'#\s*noqa:\s*\*')
BARE_NOQA = re.compile(r'#\s*noqa([^:]|$)')


class IntegrityChecker(object):
    """Checks the integrity of the docstring compared to the definition."""

    docstring = None  # type: BaseDocstring
    function = None  # type: FunctionDescription

    def __init__(self,
                 config=Configuration(
                     ignore=[],
                     message_template=None,
                     style=DocstringStyle.GOOGLE,
                     strictness=Strictness.FULL_DESCRIPTION,
                 ),
                 raise_errors=False
                 ):
        # type: (Configuration, bool) -> None
        """Create a new checker for the given function and docstring.

        Args:
            config: The configuration object for this checker.  Will
                determine which errors to show, etc.
            raise_errors: If true, we will allow ParserExceptions to
                propagate, crashing darglint.  This is mostly useful
                for development.

        """
        self.errors = list()  # type: List[DarglintError]
        self._sorted = True
        self.config = config
        self.raise_errors = raise_errors

    def run_checks(self, function):
        # type: (FunctionDescription) -> None
        """Run checks on the given function.

        Args:
            function: A function whose docstring we are verifying.

        """
        self.function = function
        if function.docstring is not None:
            try:
                if self.config.style == DocstringStyle.GOOGLE:
                    self.docstring = Docstring.from_google(
                        function.docstring,
                    )
                elif self.config.style == DocstringStyle.SPHINX:
                    self.docstring = Docstring.from_sphinx(
                        function.docstring,
                    )
                    self._check_variables()
                if self.docstring.ignore_all:
                    return
                if self.config.strictness != Strictness.FULL_DESCRIPTION:
                    if self.docstring.satisfies_strictness(
                        self.config.strictness
                    ):
                        return
                self._check_parameters()
                self._check_parameter_types()
                self._check_return()
                self._check_return_type()
                self._check_yield()
                self._check_raises()
                self._sorted = False
            except ParserException as exception:
                # If a syntax exception was raised, we may still
                # want to ignore it, if we place a noqa statement.
                if (
                    SYNTAX_NOQA.search(function.docstring)
                    or EXPLICIT_GLOBAL_NOQA.search(function.docstring)
                    or BARE_NOQA.search(function.docstring)
                ):
                    return
                if self.raise_errors:
                    raise
                self.errors.append(
                    exception.style_error(
                        self.function.function,
                        message=str(exception),
                        line_numbers=exception.line_numbers,
                    ),
                )

    def _check_parameter_types(self):
        # type: () -> None
        error_code = ParameterTypeMismatchError.error_code
        if self._ignore_error(ParameterTypeMismatchError):
            return

        argument_types = dict(
            zip(self.docstring.get_items(Sections.ARGUMENTS_SECTION) or [],
                self.docstring.get_types(Sections.ARGUMENTS_SECTION) or [])
        )
        doc_arg_types = list()  # type: List[Optional[str]]
        for name in self.function.argument_names:
            if name not in argument_types:
                doc_arg_types.append(None)
            else:
                doc_arg_types.append(argument_types[name])
        noqa_lookup = self.docstring.get_noqas()
        for name, expected, actual in zip(
                self.function.argument_names,
                self.function.argument_types,
                doc_arg_types,
        ):
            if expected is None or actual is None:
                continue
            noqa_exists = error_code in noqa_lookup
            name_has_noqa = noqa_exists and name in noqa_lookup[error_code]
            if not (expected == actual or name_has_noqa):
                default_line_numbers = self.docstring.get_line_numbers(
                    NodeType.ARGS_SECTION,
                )
                line_numbers = self.docstring.get_line_numbers_for_value(
                    NodeType.ITEM_NAME,
                    name,
                ) or default_line_numbers
                self.errors.append(
                    ParameterTypeMismatchError(
                        self.function.function,
                        name=name,
                        expected=expected,
                        actual=actual,
                        line_numbers=line_numbers,
                    )
                )

    def _check_return_type(self):
        # type: () -> None
        if self._ignore_error(ReturnTypeMismatchError):
            return

        fun_type = self.function.return_type
        doc_type = self.docstring.get_types(Sections.RETURNS_SECTION)
        if not doc_type or isinstance(doc_type, list):
            doc_type = None
        if fun_type is not None and doc_type is not None:
            if fun_type != doc_type:
                line_numbers = self.docstring.get_line_numbers(
                    NodeType.RETURNS_SECTION,
                )
                self.errors.append(
                    ReturnTypeMismatchError(
                        self.function.function,
                        expected=fun_type,
                        actual=doc_type,
                        line_numbers=line_numbers,
                    ),
                )

    def _check_yield(self):
        # type: () -> None
        doc_yield = self.docstring.get_section(Sections.YIELDS_SECTION)
        fun_yield = self.function.has_yield
        ignore_missing = self._ignore_error(MissingYieldError)
        ignore_excess = self._ignore_error(ExcessYieldError)
        if fun_yield and not doc_yield and not ignore_missing:
            self.errors.append(
                MissingYieldError(self.function.function)
            )
        elif doc_yield and not fun_yield and not ignore_excess:
            line_numbers = self.docstring.get_line_numbers(
                NodeType.YIELDS_SECTION,
            )
            self.errors.append(
                ExcessYieldError(
                    self.function.function,
                    line_numbers=line_numbers,
                )
            )

    def _check_return(self):
        # type: () -> None
        doc_return = self.docstring.get_section(Sections.RETURNS_SECTION)
        fun_return = self.function.has_return
        ignore_missing = self._ignore_error(MissingReturnError)
        ignore_excess = self._ignore_error(ExcessReturnError)
        if fun_return and not doc_return and not ignore_missing:
            self.errors.append(
                MissingReturnError(self.function.function)
            )
        elif doc_return and not fun_return and not ignore_excess:
            line_numbers = self.docstring.get_line_numbers(
                NodeType.RETURNS_SECTION,
            )
            self.errors.append(
                ExcessReturnError(
                    self.function.function,
                    line_numbers=line_numbers,
                )
            )

    def _check_parameters(self):
        # type: () -> None
        # argument_types = self.docstring.get_argument_types()
        # docstring_arguments = set(argument_types.keys())
        docstring_arguments = set(self.docstring.get_items(
            Sections.ARGUMENTS_SECTION
        ) or [])
        actual_arguments = set(self.function.argument_names)
        missing_in_doc = actual_arguments - docstring_arguments
        missing_in_doc = self._remove_ignored(
            missing_in_doc,
            MissingParameterError,
        )

        # Get a default line number.
        default_line_numbers = self.docstring.get_line_numbers(
            NodeType.ARGS_SECTION
        )

        for missing in missing_in_doc:
            # We use the default line numbers because a missing
            # parameter, by definition, will not have line numbers.
            self.errors.append(
                MissingParameterError(
                    self.function.function,
                    missing,
                    line_numbers=default_line_numbers
                )
            )

        missing_in_function = docstring_arguments - actual_arguments
        missing_in_function = self._remove_ignored(
            missing_in_function,
            ExcessParameterError,
        )
        for missing in missing_in_function:
            line_numbers = self.docstring.get_line_numbers_for_value(
                NodeType.ARGS_SECTION,
                missing,
            ) or default_line_numbers
            self.errors.append(
                ExcessParameterError(
                    self.function.function,
                    missing,
                    line_numbers=line_numbers,
                )
            )

        for definition in self.docstring.get_definitions(Sections.ARGUMENTS_SECTION) or []:
            if not definition.endswith('.'):
                line_numbers = self.docstring.get_line_numbers_for_value(
                    NodeType.ARGS_SECTION,
                    definition,
                ) or default_line_numbers
                self.errors.append(
                    DefinitionNotEndingWithPeriodError(
                        self.function.function,
                        definition,
                        line_numbers=line_numbers,
                    )
                )
            if definition[0] != definition[0].upper():
                line_numbers = self.docstring.get_line_numbers_for_value(
                    NodeType.ARGS_SECTION,
                    definition,
                ) or default_line_numbers
                self.errors.append(
                    DefinitionNotStartingWithCapitalError(
                        self.function.function,
                        definition,
                        line_numbers=line_numbers,
                    )
                )


    def _check_variables(self):
        # type: () -> None
        described_variables = set(
            self.docstring.get_items(Sections.VARIABLES_SECTION) or []
        )  # type: Set[str]
        actual_variables = set(self.function.variables)
        excess_in_doc = described_variables - actual_variables

        # Get a default line number.
        default_line_numbers = self.docstring.get_line_numbers(
            NodeType.VARIABLES_SECTION
        )

        for excess in excess_in_doc:
            line_numbers = self.docstring.get_line_numbers_for_value(
                NodeType.VARIABLES_SECTION,
                excess,
            ) or default_line_numbers
            self.errors.append(
                ExcessVariableError(
                    self.function.function,
                    excess,
                    line_numbers=line_numbers,
                )
            )

    def _ignore_error(self, error):
        # type: (Any) -> bool
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
        noqa_lookup = self.docstring.get_noqas()
        inline_error = error_code in noqa_lookup
        if inline_error and not noqa_lookup[error_code]:
            return True
        return False

    def _remove_ignored(self, missing, error):
        # type: (Set[str], Any) -> Set[str]
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
        noqa_lookup = self.docstring.get_noqas()
        inline_ignore = error_code in noqa_lookup
        if not inline_ignore:
            return missing

        # We are to ignore specific instances.
        return missing - set(noqa_lookup[error_code])

    def _check_raises(self):
        # type: () -> None
        exception_types = self.docstring.get_items(Sections.RAISES_SECTION)
        docstring_raises = set(exception_types or [])
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
        default_line_numbers = self.docstring.get_line_numbers(
            NodeType.RAISES_SECTION,
        )
        for missing in missing_in_function:
            line_numbers = self.docstring.get_line_numbers_for_value(
                NodeType.RAISES_SECTION,
                missing,
            ) or default_line_numbers
            self.errors.append(
                ExcessRaiseError(
                    self.function.function,
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
