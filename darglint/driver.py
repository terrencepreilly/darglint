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
    default=2,
    type=int,
    choices=[1, 2, 3],
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


def get_headers(filenames):
    """Get the headers to separate the descriptions."""
    return [
        ('*' * 20) + ' {} '.format(filename) + ('*' * (40 - len(filename)))
        for filename in filenames
    ]


def get_error_report(filename, verbosity):
    """Get the error report for the given file."""
    program = read_program(filename)
    tree = ast.parse(program)
    functions = get_function_descriptions(tree)
    checker = IntegrityChecker()
    for function in functions:
        checker.run_checks(function)
    return checker.get_error_report(verbosity)


def main():
    """Run darglint.

    Called as a script when setup.py is installed.

    """
    args = parser.parse_args()
    files = [x for x in args.files if x.endswith('.py')]
    verbosity = args.verbosity
    headers = get_headers(files)
    for filename, header in zip(files, headers):
        # if there are errors, then display the header
        # and the errors, otherwise don't display anything.
        error_report = get_error_report(filename, verbosity)
        if len(error_report) > 0:
            print(header)
            print(error_report + '\n')


if __name__ == '__main__':
    main()
