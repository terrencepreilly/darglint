"""The entry point for flake8."""

import ast  # noqa
from typing import (  # noqa
    Iterator,
    Tuple,
)

from .function_description import (
    get_function_descriptions,
)
from .integrity_checker import IntegrityChecker
from .config import (
    get_config,
)


__version__ = '0.4.1'


class DarglintChecker(object):

    name = 'flake8-darglint'
    version = __version__

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename
        self.verbosity = 2
        self.config = get_config()

    def run(self):
        # type: () -> Iterator[Tuple[int, int, str, type]]
        if '*' in self.config.ignore:
            return

        # Remember the last line number, so that if there is an
        # exception raised by Darglint, we can at least give a decent
        # idea of where it was raised.
        last_line = 1
        try:
            functions = get_function_descriptions(self.tree)
            checker = IntegrityChecker(
                self.config,
                raise_errors=False,
            )
            for function in functions:
                checker.run_checks(function)

            error_report = checker.get_error_report(
                self.verbosity,
                self.filename
            )
            for line, col, msg in error_report.flake8_report():
                last_line = line
                yield (line, col, msg, type(self))

        except Exception as ex:
            yield (last_line, 0, str(ex), type(self))
