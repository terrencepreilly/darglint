"""The entry point for flake8."""

import ast  # noqa
from typing import (  # noqa
    Iterator,
    Tuple,
)

from .docstring.base import DocstringStyle
from .function_description import (
    get_function_descriptions,
)
from .integrity_checker import IntegrityChecker
from .config import (
    Configuration,
    get_config,
    Strictness,
)


__version__ = '1.5.5'


class DarglintChecker(object):

    name = 'flake8-darglint'
    version = __version__
    config = get_config()

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename
        self.verbosity = 2

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
                raise_errors=False,
            )
            checker.config = self.config
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
            yield (
                last_line,
                0,
                'DAR000: Unexpected exception in darglint: ' + str(ex),
                type(self)
            )

    @classmethod
    def add_options(cls, option_manager):
        defaults = cls.config

        option_manager.add_option(
            '--docstring-style',
            default=defaults.style.name,
            parse_from_config=True,
            help='Docstring style to use for Darglint',
        )

        option_manager.add_option(
            '--strictness',
            default=defaults.strictness.name,
            parse_from_config=True,
            help='Strictness level to use for Darglint',
        )

    @classmethod
    def parse_options(cls, options):
        cls.config.style = DocstringStyle.from_string(options.docstring_style)
        cls.config.strictness = Strictness.from_string(options.strictness)
