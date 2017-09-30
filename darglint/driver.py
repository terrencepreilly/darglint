"""Defines the command line interface for darglint."""
import sys
from typing import List

from redbaron import RedBaron

from .darglint import (
    get_functions_and_docstrings,
    read_program,
)
from .lex import lex
from .parse import parse_arguments


def _print_error_message(
        procedure_name: str,
        docstring_arguments: List[str],
        actual_arguments: List[str]) -> None:
    print('{}'.format(procedure_name))
    missing_in_doc = actual_arguments - docstring_arguments
    missing_in_fun = docstring_arguments - actual_arguments
    if len(missing_in_doc) > 0:
        for missing in missing_in_doc:
            print('  - {}'.format(missing))
    if len(missing_in_fun) > 0:
        for missing in missing_in_fun:
            print('  + {}'.format(missing))
    print()


def main():
    """Check the parameters of all functions and methods."""
    program = read_program(sys.argv[1])
    red = RedBaron(program)
    functions = get_functions_and_docstrings(red.fst())
    for name, argnames, has_return, docstring in functions:
        docstring_arguments = set(parse_arguments(lex(docstring)))
        actual_arguments = set(argnames) - {'self'}
        if len(docstring_arguments) != len(actual_arguments):
            _print_error_message(
                name,
                docstring_arguments,
                actual_arguments,
            )


if __name__ == '__main__':
    main()
