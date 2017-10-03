"""Defines the command line interface for darglint."""
import ast
import sys
from typing import List

from .darglint import (
    read_program,
    FunctionDescription,
    get_function_descriptions,
)
from .lex import lex
from .parse import parse_arguments
from .errors import (
    DarglintError,
    MissingParameterError,
    ExcessParameterError,
)


class IntegrityChecker(object):
    """Checks the integrity of the docstring compared to the definition."""

    def __init__(self, function: FunctionDescription):
        """Create a new checker for the given function and docstring."""
        self.function = function
        self.errors = list()  # type: List[DarglintError]
        self._run_checks()

    def _run_checks(self):
        self._check_parameters()

    def _check_parameters(self):
        docstring = self.function.docstring
        docstring_arguments = set(parse_arguments(lex(docstring)))
        actual_arguments = set(self.function.argument_names)
        missing_in_doc = actual_arguments - docstring_arguments
        for missing in missing_in_doc:
            self.errors.append(
                MissingParameterError(self.function.line_number)
            )
        missing_in_function = docstring_arguments - actual_arguments
        for missing in missing_in_function:
            self.errors.append(
                ExcessParameterError(self.function.line_number)
            )

    def __iter__(self):
        """Get the iterator."""
        return self

    def __next__(self) -> DarglintError:
        """Get the next error in the function."""
        if len(self.errors) > 0:
            return self.errors.pop()
        else:
            raise StopIteration


def _print_error_message(
        function: FunctionDescription,
        docstring_arguments: List[str]
) -> None:
    print('{}: {}'.format(function.line_number, function.name))
    docargs = set(docstring_arguments)
    funargs = set(function.argument_names)
    missing_in_doc = funargs - docargs
    missing_in_fun = docargs - funargs
    if len(missing_in_doc) > 0:
        for missing in missing_in_doc:
            print('  - {}'.format(missing))
    if len(missing_in_fun) > 0:
        for missing in missing_in_fun:
            print('  + {}'.format(missing))


def main():
    """Check the parameters of all functions and methods."""
    program = read_program(sys.argv[1])
    tree = ast.parse(program)
    functions = get_function_descriptions(tree)
    functions.sort(key=lambda x: x.line_number)
    for function in functions:
        if function.docstring is None:
            continue
        # NOTE: This line has caused several problems. Consider rewrite.
        docstring_arguments = set(parse_arguments(lex(function.docstring)))
        actual_arguments = set(function.argument_names)
        if len(docstring_arguments) != len(actual_arguments):
            _print_error_message(function, docstring_arguments)


if __name__ == '__main__':
    main()
