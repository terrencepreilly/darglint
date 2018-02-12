"""Defines the command line interface for darglint."""
import argparse
import ast

from .function_description import (
    read_program,
    get_function_descriptions,
)
from .integrity_checker import IntegrityChecker
from .config import (
    Configuration,
    get_config,
)


# ---------------------- ARGUMENT PARSER -----------------------------

parser = argparse.ArgumentParser(description='Check docstring validity.')
parser.add_argument(
    '--message-template',
    '-m',
    type=str,
    help=(
        'Specify a message template.  This is a Python format string '
        'describing errors, which can access the following attributes:\n'
        '    line: The line number,\n'
        '    msg: The error message,\n'
        '    msg_id: The error code,\n'
        '    obj: The function/method name,\n'
        '    path: The relative file path.\n'
    ),
)
parser.add_argument(
    '--raise-syntax',
    action='store_true',
    help=(
        'When a docstring is incorrectly formatted, raise an exception '
        'rather than storing the error.'
    ),
)
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


def get_error_report(filename,
                     verbosity,
                     config,
                     raise_errors_for_syntax,
                     message_template=None,
    ):
    # type: (str, int, Configuration, bool, str) -> str
    """Get the error report for the given file.

    Args:
        filename: The name of the module to check.
        verbosity: The level of verbosity, in the range [1, 3].
        config: The configuration for the error report.
        raise_errors_for_syntax: True if we want parser errors
            to propagate up (crashing darglint.)  This is useful
            if we are developing on darglint -- we can get the stack
            trace and know exactly where darglint failed.
        message_template: A python format string for specifying
            how the message should appear to the user.

    Returns:
        An error report for the file.

    """
    program = read_program(filename)
    tree = ast.parse(program)
    functions = get_function_descriptions(tree)
    checker = IntegrityChecker(
        config,
        raise_errors=raise_errors_for_syntax,
    )
    for function in functions:
        checker.run_checks(function)
    return checker.get_error_report(
        verbosity,
        filename,
        message_template=message_template,
    )


def main():
    # type: () -> None
    """Run darglint.

    Called as a script when setup.py is installed.

    """
    config = get_config()
    args = parser.parse_args()
    files = [x for x in args.files if x.endswith('.py')]
    raise_errors_for_syntax = args.raise_syntax or False
    for filename in files:
        error_report = get_error_report(
            filename,
            args.verbosity,
            config,
            raise_errors_for_syntax,
            message_template=args.message_template,
        )
        if error_report:
            print(error_report + '\n')


if __name__ == '__main__':
    main()
