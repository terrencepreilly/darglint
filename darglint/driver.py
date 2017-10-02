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
