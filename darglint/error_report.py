"""The error reporting classes."""

import ast
from collections import defaultdict, OrderedDict
from typing import (
    Dict,
    Iterable,
    List,
    Set,
)

from .errors import DarglintError


class ErrorReport(object):
    """A base error report class.

    To extend the error report class, the staticmethods below
    (new_current_errors, add_to_current_errors, and
    current_errors_to_list), should be overridden.
    """

    def __init__(self, errors: List[DarglintError]):
        """Create a new error report.

        Args:
            errors: A list of DarglintError instances.

        """
        self.errors = errors

    @staticmethod
    def new_current_errors() -> Iterable:
        """Get a new collection to store the errors of the current function.

        Raises:
            NotImplementError: Always.  Must be overriden.

        """
        raise NotImplemented()

    @staticmethod
    def add_to_current_errors(current_errors: Iterable,
                              error: DarglintError) -> Iterable:
        """Add an error to the collection of errors of the current function.

        Args:
            current_errors: The collection of DarglintErrors so far.
            error: The error to add to this collection.

        Raises:
            NotImplementError: Always.  Must be overriden.

        """
        raise NotImplemented()

    @staticmethod
    def current_errors_to_list(current_errors: Iterable) -> List[str]:
        """Render the collection of errors for the current function.

        Args:
            current_errors: The collection of DarglintErrors for a function.

        Raises:
            NotImplementError: Always.  Must be overriden.

        """
        raise NotImplemented()

    def _sort(self):
        self.errors.sort(key=lambda x: x.function.lineno)

    def _group_errors_by_function(self):
        self._sort()
        self.error_dict = OrderedDict()
        current = None  # The current function
        for error in self.errors:
            if current != error.function:
                current = error.function
                self.error_dict[current] = list()
            self.error_dict[current].append(error)

    def get_function_description(self, function: ast.FunctionDef) -> str:
        """Get the function description.

        Args:
            function: The function to describe.

        Returns:
            A string representing the function divider.

        """
        return '{} {}'.format(function.lineno, function.name)

    def __str__(self) -> str:
        """Return a string representation of this error report.

        Returns:
            A string representation of this error report.

        """
        if len(self.errors) == 0:
            return ''
        self._group_errors_by_function()
        ret = list()
        for function in self.error_dict:
            function_description = self.get_function_description(function)
            ret.append(function_description)
            current_errors = self.new_current_errors()
            for error in self.error_dict[function]:
                current_errors = self.add_to_current_errors(
                    current_errors, error
                )
            ret.extend(self.current_errors_to_list(current_errors))
        return '\n'.join(ret)


class LowVerbosityErrorReport(ErrorReport):
    """An error report with a moderate amount of verbosity.

    Errors will be rendered as such:

        <linenumber> <function name>
            <general error message>
            <general error message>
            ...
        ...

    """

    @staticmethod
    def new_current_errors() -> Set[str]:
        """Get a new collection to store the errors of the current function.

        Returns:
            An empty set.

        """
        return set()

    @staticmethod
    def add_to_current_errors(current_errors: Set[str],
                              error: DarglintError) -> Set[str]:
        """Add an error to the collection of errors of the current function.

        Args:
            current_errors: The collection of DarglintErrors so far.
            error: The error to add to this collection.

        Returns:
            The updated instance of the collection.

        """
        return current_errors | {
            '{} {}.'.format(error.error_code, error.general_message)
        }

    @staticmethod
    def current_errors_to_list(current_errors: Set[str]) -> List[str]:
        """Render the collection of errors for the current function.

        Args:
            current_errors: The collection of DarglintErrors for a function.

        Returns:
            A list of strings.

        """
        return sorted(['  {}'.format(x) for x in current_errors])


class MidVerbosityErrorReport(ErrorReport):
    """An error report with a moderate amount of verbosity.

    Errors will be rendered as such:

        <linenumber> <function name>
            <general error message>: <terse error messages>
            <general error message>: <terse error messages>
            ...
        ...

    """

    @staticmethod
    def new_current_errors() -> Dict[str, List[str]]:
        """Get a new collection to store the errors of the current function.

        Returns:
            A dictionary containing the general error message as a key,
            and a list of terse error messages as a value.

        """
        return defaultdict(list)

    @staticmethod
    def add_to_current_errors(current_errors: Dict[str, List[str]],
                              error: DarglintError) -> Dict[str, List[str]]:
        """Add an error to the collection of errors of the current function.

        Args:
            current_errors: The collection of DarglintErrors so far.
            error: The error to add to this collection.

        Returns:
            The updated instance of the collection.

        """
        error_class = '{} {}'.format(error.error_code, error.general_message)
        current_errors[error_class].append(error.terse_message)
        return current_errors

    @staticmethod
    def current_errors_to_list(
            current_errors: Dict[str, List[str]]) -> List[str]:
        """Render the collection of errors for the current function.

        Args:
            current_errors: The collection of DarglintErrors for a function.

        Returns:
            A list of strings.

        """
        ret = list()
        returns = list()  # Return statements should come last.
        for general in current_errors:
            if 'Returns' in general or 'Yields' in general:
                returns.append('  {}.'.format(general))
            else:
                ret.append('  {}: {}'.format(
                    general, ', '.join(current_errors[general])
                ))
        ret.extend(returns)
        return ret


class HighVerbosityErrorReport(ErrorReport):
    """An error report with a high amount of verbosity.

    Errors will be rendered as such:

        <linenumber> <function name>
            <error message>
            <error message>
            ...
        ...

    Where the error messages describe each instance of the error in some
    amount of detail.

    """

    @staticmethod
    def new_current_errors() -> List[str]:
        """Get a new collection to store the errors of the current function.

        Returns:
            An empty list.

        """
        return list()

    @staticmethod
    def add_to_current_errors(current_errors: List[str],
                              error: DarglintError) -> List[str]:
        """Add an error to the collection of errors of the current function.

        Args:
            current_errors: The collection of DarglintErrors so far.
            error: The error to add to this collection.

        Returns:
            The updated instance of the collection.

        """
        current_errors.append('  ' + error.message)
        return current_errors

    @staticmethod
    def current_errors_to_list(current_errors: List[str]) -> List[str]:
        """Render the collection of errors for the current function.

        Args:
            current_errors: The collection of DarglintErrors for a function.

        Returns:
            A list of strings.

        """
        return current_errors
