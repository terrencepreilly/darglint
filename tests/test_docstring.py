"""Tests for the Docstring class."""

from unittest import TestCase

from darglint.docstring import Docstring
from darglint.lex import lex
from darglint.parse import parse
from darglint.peaker import Peaker


class DocstringMethodTest(TestCase):
    """Tests for the Docstring class."""

    def test_global_noqa_no_body(self):
        """Ensure an empty noqa body means ignore everything."""
        root = parse(Peaker(lex('\n'.join([
            'A short explanation.',
            '',
            '    # noqa',
            '\n',
        ])), lookahead=3))
        docstring = Docstring(root)
        self.assertTrue(docstring.ignore_all)

    def test_global_noqa_star_body(self):
        """Ensure noqa with * means ignore everything."""
        root = parse(Peaker(lex('\n'.join([
            'A short explanation.',
            '',
            '    # noqa: *',
            '\n',
        ])), lookahead=3))
        docstring = Docstring(root)
        self.assertTrue(docstring.ignore_all)

    def test_get_short_description(self):
        """Ensure we can get the short description."""
        root = parse(Peaker(lex('Nothing but a short description.'), lookahead=3))
        docstring = Docstring(root)
        self.assertEqual(
            docstring.short_description,
            'Nothing but a short description.'
        )
