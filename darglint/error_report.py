"""The error reporting classes."""

import ast  # noqa
from collections import OrderedDict
from typing import (  # noqa
    Dict,
    Iterator,
    List,
    Tuple,
    Union,
)
from .function_description import (
    get_line_number_from_function,
)

from .errors import DarglintError  # noqa


class ErrorReport(object):
    """Reports the errors for the given run."""

    def __init__(
        self,
        errors,
        filename,
        verbosity=2,
        message_template=None,
    ):
        # type: (List[DarglintError], str, int, str) -> None
        """Create a new error report.

        Args:
            errors: A list of DarglintError instances.
            filename: The name of the file the error came from.
            verbosity: A number in the set, {1, 2}, representing low
                and high verbosity.
            message_template: A python format string for specifying
                how the string representation of this ErrorReport
                should appear.

        """
        self.filename = filename
        self.verbosity = verbosity
        self.errors = errors
        self.error_dict = self._group_errors_by_function()
        if message_template is None:
            self.message_template = '{path}:{obj}:{line}: {msg_id}: {msg}'
        else:
            self.message_template = message_template

    def _sort(self):
        # type: () -> None
        self.errors.sort(key=lambda x: x.function.lineno)

    def _group_errors_by_function(self):
        # type: () -> Dict[Union[ast.FunctionDef, ast.AsyncFunctionDef], List[DarglintError]]  # noqa: E501
        """Sort the current errors by function, and put into an OrderedDict.

        Returns:
            An ordered dictionary of functions and their errors.

        """
        self._sort()
        error_dict = OrderedDict()  # type: Dict
        current = None  # The current function
        for error in self.errors:
            if current != error.function:
                current = error.function
                error_dict[current] = list()
            error_dict[current].append(error)

        # Sort all of the errors returned by the function
        # alphabetically.
        for key in error_dict:
            error_dict[key].sort(key=lambda x: x.message() or '')

        # Sort all of the errors returned by the key
        # by the line numbers.
        for key in error_dict:
            error_dict[key].sort(key=lambda x: x.line_numbers or (0, 0))

        return error_dict

    def _get_error_description(self, error):  # type: (DarglintError) -> str
        """Get the error description.

        Args:
            error: The error to describe.

        Returns:
            A string representing the error.

        """
        line_number = get_line_number_from_function(error.function)
        if (hasattr(error.function, 'decorator_list')
                and error.function.decorator_list):
            line_number += len(error.function.decorator_list)
        if error.line_numbers:
            line_number += error.line_numbers[0] + 1
        return self.message_template.format(
            msg_id=error.error_code,
            msg=error.message(verbosity=self.verbosity),
            path=self.filename,
            obj=error.function.name,
            line=line_number,  # error.function.lineno,
        )

    def __str__(self):  # type: () -> str
        """Return a string representation of this error report.

        Returns:
            A string representation of this error report.

        """
        if len(self.errors) == 0:
            return ''
        ret = list()
        for function in self.error_dict:
            for error in self.error_dict[function]:
                ret.append(self._get_error_description(error))
        return '\n'.join(ret)

    def flake8_report(self):
        # type: () -> Iterator[Tuple[int, int, str]]
        # line, col, message
        for function in self.error_dict:
            for error in self.error_dict[function]:
                # TODO: Shouldn't get_line_number (here and above) return
                # the correct line number?  Why do we have to handle decorators
                # here?
                line_number = get_line_number_from_function(error.function)
                if (hasattr(error.function, 'decorator_list')
                        and error.function.decorator_list):
                    line_number += len(error.function.decorator_list)
                if error.line_numbers:
                    line_number += error.line_numbers[0] + 1
                else:
                    line_number += 1
                # TODO: Do we need verbosity here?
                message = '{} {}'.format(
                    error.error_code,
                    error.message(self.verbosity),
                )
                yield (line_number, 0, message)
