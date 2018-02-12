"""The error reporting classes."""

import ast
from collections import OrderedDict
from typing import (
    Dict,
    List,
)

from .errors import DarglintError


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
        # type: () -> Dict[ast.FunctionDef, List[DarglintError]]
        """Sort the current errors by function, and put into an OrderedDict.

        Returns:
            An ordered dictionary of funcitons and their errors.

        """
        self._sort()
        error_dict = OrderedDict() # type: Dict[ast.FunctionDef, List[DarglintError]]
        current = None  # The current function
        for error in self.errors:
            if current != error.function:
                current = error.function
                error_dict[current] = list()
            error_dict[current].append(error)
        return error_dict

    def _get_error_description(self, error): # type: (DarglintError) -> str
        """Get the error description.

        Args:
            error: The error to describe.

        Returns:
            A string representing the error.

        """
        return self.message_template.format(
            msg_id=error.error_code,
            msg=error.message(verbosity=self.verbosity),
            path=self.filename,
            obj=error.function.name,
            line=error.function.lineno,
        )

    def __str__(self): # type: () -> str
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
