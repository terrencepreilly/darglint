from unittest import TestCase

from flake8.options.manager import OptionManager

from darglint.config import get_config
from darglint.docstring.style import DocstringStyle
from darglint.flake8_entry import DarglintChecker
from darglint.strictness import Strictness

class Flake8TestCase(TestCase):
    """Tests that flake8 config is parsed correctly."""

    def test_config_parsed(self):
        default_config = get_config().get_default_instance()
        parser = OptionManager('', '')
        DarglintChecker.add_options(parser)

        options, args = parser.parse_args([])
        DarglintChecker.parse_options(options)
        self.assertEqual(default_config.style, DarglintChecker.config.style)

        argv = [
            '--docstring-style=numpy',
            '--strictness=short'
        ]
        options, args = parser.parse_args(argv)

        DarglintChecker.config = default_config
        DarglintChecker.parse_options(options)
        self.assertEqual(DarglintChecker.config.style, DocstringStyle.NUMPY)
        self.assertEqual(DarglintChecker.config.strictness, Strictness.SHORT_DESCRIPTION)
