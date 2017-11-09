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

    def __init__(self,
                 errors: List[DarglintError],
                 filename: str,
                 verbosity: int=2):
        """Create a new error report.

        Args:
            errors: A list of DarglintError instances.
            filename: The name of the file the error came from.
            verbosity: A number in the set, {1, 2}, representing low
                and high verbosity.

        """
        self.filename = filename
        self.verbosity = verbosity
        self.errors = errors
        self.error_dict = self._group_errors_by_function()

    def _sort(self):
        self.errors.sort(key=lambda x: x.function.lineno)

    def _group_errors_by_function(
            self) -> Dict[ast.FunctionDef, DarglintError]:
        """Sort the current errors by function, and put into an OrderedDict.

        Returns:
            An ordered dictionary of funcitons and their errors.

        """
        self._sort()
        error_dict = OrderedDict()
        current = None  # The current function
        for error in self.errors:
            if current != error.function:
                current = error.function
                error_dict[current] = list()
            error_dict[current].append(error)
        return error_dict

    def _get_error_description(self, error) -> str:
        """Get the error description.

        Args:
            error: The error to describe.

        Returns:
            A string representing the error.

        """
        return '{}:{}:{}: {}'.format(
            self.filename,
            error.function.name,
            error.function.lineno,
            error.message(verbosity=self.verbosity),
        )

    def __str__(self) -> str:
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
