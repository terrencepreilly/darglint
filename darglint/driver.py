"""Defines the command line interface for darglint."""
import argparse
import ast
import pathlib
import sys

from .function_description import (
    read_program,
    get_function_descriptions,
)
from .integrity_checker import IntegrityChecker
from .config import (  # noqa
    Configuration,
    get_config,
)
from .docstring.base import DocstringStyle


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
        'rather than storing the error.  Useful for debugging darglint.'
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
    '--version',
    action='store_true',
    help=(
        'Return the current version number of darglint.'
    ),
)
parser.add_argument(
    'files',
    nargs='*',
    help=(
        'The python source files to check. If "-" is given, then stdin will '
        'be read.'
    ),
)
parser.add_argument(
    '--no-exit-code',
    '-x',
    action='store_true',
    help=(
        'Exit with status 0, even on errors.  By default, darglint '
        'exits with status 1 when errors are encountered.  Giving '
        'this flag prevents that.  Useful when invocating with xargs '
        'and you want to see all errors.  '
        'Ex: `find . -name "*.py" | xargs darglint -x`'
    ),
)
parser.add_argument(
    '--list-errors',
    action='store_true',
    help=(
        'Print a list of error codes and what they represent.'
    )
)
parser.add_argument(
    '-s',
    '--docstring-style',
    default=None,
    choices=['google', 'sphinx'],
    help=(
        'The docstring style used in the given project. Currently, '
        'only google or sphinx styles are supported.'
    )
)
parser.add_argument(
    '--raise-on-missing-docstrings',
    action='store_true',
    help=(
        'Missing docstrings for public functions or methods are considered an '
        'error.'
    )
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
    return checker.get_error_report_string(
        verbosity,
        filename,
        message_template=message_template,
    )


def print_error_list():
    print('\n'.join([
        'I002: Missing docstring for public method.'
        'I003: Missing docstring for public function.'
        'I101: The docstring is missing a parameter in the definition.',
        'I102: The docstring contains a parameter not in function.',
        'I103: The docstring parameter type doesn\'t match function.',
        'I201: The docstring is missing a return from definition.',
        'I202: The docstring has a return not in definition.',
        'I203: The docstring parameter type doesn\'t match function.',
        'I301: The docstring is missing a yield present in definition.',
        'I302: The docstring has a yield not in definition.',
        'I401: The docstring is missing an exception raised.',
        'I402: The docstring describes an exception not explicitly raised.',
        'S001: Describes that something went wrong in parsing the docstring.',
        'S002: An argument/exception lacks a description.',
    ]))


def print_version():
    print('0.5.7')


def main():
    # type: () -> None
    """Run darglint.

    Called as a script when setup.py is installed.

    """
    args = parser.parse_args()
    exit_code = not args.no_exit_code
    encountered_errors = False

    if args.list_errors:
        print_error_list()
        sys.exit(0)

    if args.version:
        print_version()

    # Expand directories.
    files = []
    for f in args.files:
        p = pathlib.Path(f)
        if not p.is_dir():
            files.append(f)
        # Convert back to strings to not require modifications of any
        # subsequent code.
        files.extend(str(i) for i in p.glob('**/*.py'))

    try:
        config = get_config()
        if args.docstring_style == 'sphinx':
            config.style = DocstringStyle.SPHINX
        elif args.docstring_style == 'google':
            config.style = DocstringStyle.GOOGLE

        if args.raise_on_missing_docstrings:
            config.raise_on_missing_docstrings = True

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
                encountered_errors = True
    except Exception as exc:
        # Exit with status 129 regardless of whether user wants a
        # exit code or not -- darglint failed, and it should
        # look like it failed.
        print(exc, file=sys.stderr)
        sys.exit(129)
    if encountered_errors and exit_code:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
