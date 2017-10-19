"""Defines the command line interface for darglint."""
import argparse
import ast

from .darglint import (
    read_program,
    get_function_descriptions,
)
from .integrity_checker import IntegrityChecker


# ---------------------- ARGUMENT PARSER -----------------------------

parser = argparse.ArgumentParser(description='Check docstring validity.')
parser.add_argument(
    '--verbosity',
    '-v',
    default=1,
    type=int,
    choices=[1, 2],
    help='The level of verbosity.',
)
parser.add_argument(
    'files',
    nargs='+',
    help=(
        'The python source files to check.  Any files not ending in '
        '".py" are ignored.'
    ),
)

# ---------------------- MAIN SCRIPT ---------------------------------


def get_error_report(filename: str, verbosity: int) -> str:
    """Get the error report for the given file.

    Args:
        filename: The name of the module to check.
        verbosity: The level of verbosity, in the range [1, 3].

    Returns:
        An error report for the file.

    """
    program = read_program(filename)
    tree = ast.parse(program)
    functions = get_function_descriptions(tree)
    checker = IntegrityChecker()
    for function in functions:
        checker.run_checks(function)
    return checker.get_error_report(verbosity, filename)


def main():
    """Run darglint.

    Called as a script when setup.py is installed.

    """
    args = parser.parse_args()
    files = [x for x in args.files if x.endswith('.py')]
    verbosity = args.verbosity
    for filename in files:
        error_report = get_error_report(filename, verbosity)
        if len(error_report) > 0:
            print(error_report + '\n')


if __name__ == '__main__':
    main()
