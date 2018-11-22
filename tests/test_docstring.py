"""Tests for the Docstring class."""

from unittest import TestCase
from random import shuffle

from darglint.docstring.base import Sections
from darglint.docstring.docstring import Docstring
from darglint.lex import lex
from darglint.parse import google
from darglint.parse import sphinx
from darglint.peaker import Peaker


class DocstringBaseMethodTests(TestCase):

    # A set of equivalent docstrings, in each of the representations.
    # These should evaluate to the same for each of the base methods.
    _equivalent_docstrings = [
        # (
        #     '\n'.join([
        #         'Only a short description.',
        #     ]),
        #     '\n'.join([
        #         'Only a short description.',
        #     ])
        # ),
        # (
        #     '\n'.join([
        #         'A single item and type.',
        #         '',
        #         'Args:',
        #         '    x (int): A number.',
        #         '',
        #     ]),
        #     '\n'.join([
        #         'A single item and type.',
        #         '',
        #         ':param x: A number.',
        #         ':type x: int',
        #         '',
        #     ])
        # ),
        # (
        #     '\n'.join([
        #         'A docstring with noqas in it.',
        #         '',
        #         '# noqa: I203',
        #         '',
        #         '# noqa',
        #         '',
        #     ]),
        #     '\n'.join([
        #         'A docstring with noqas in it.',
        #         '',
        #         '# noqa: I203',
        #         '',
        #         '# noqa',
        #         '',
        #     ])
        # ),
        # (
        #     '\n'.join([
        #         'A docstring with types in it.',
        #         '',
        #         'Args:',
        #         '    x (int): The number to double.',
        #         '',
        #         'Returns:',
        #         '    int: The number, doubled.',
        #         '',
        #     ]),
        #     '\n'.join([
        #         'A docstring with types in it.',
        #         '',
        #         ':param x: The number to double.',
        #         ':type x: int',
        #         ':returns: The number, doubled.',
        #         ':rtype: int',
        #         '',
        #     ])
        # ),
        (
            '\n'.join([
                'A very complete docstring.',
                '',
                'There is a long-description section.',
                '',
                '    code example',
                '',
                'And it continues over multiple lines.',
                '',
                'Args:',
                '    x (int): The first integer.  This description ',
                '        spans multiple lines.',
                '    y (int): The second integer.',
                '',
                'Raises:',
                '    InvalidNumberException: An exception for if it\'s '
                '        invalid.',
                '    Exception: Seemingly at random.',
                '',
                'Yields:',
                '    int: Numbers that were calculated somehow.',
                '',
            ]),
            '\n'.join([
                'A very complete docstring.',
                '',
                'There is a long-description section.',
                '',
                '    code example',
                '',
                'And it continues over multiple lines.',
                '',
                ':param x: The first integer.  This description ',
                '    spans multiple lines.',
                ':type x: int',
                ':param y: The second integer.',
                ':type y: int',
                ':raises InvalidNumberException: An exception for if it\'s '
                '    invalid.',
                ':raises Exception: Seemingly at random.',
                ':yields: Numbers that were calculated somehow.',
                ':ytype: int',
                '',
            ])
        ),
    ]

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.equivalent_docstrings = list()
        for google_doc, sphinx_doc in cls._equivalent_docstrings:
            google_root = google.parse(Peaker(lex(google_doc), 3))
            sphinx_root = sphinx.parse(Peaker(lex(sphinx_doc), 2))
            cls.equivalent_docstrings.append((
                Docstring.from_google(google_root),
                Docstring.from_sphinx(sphinx_root),
            ))

    # Get section (section)
    def test_get_section_equivalency(self):
        for google_doc, sphinx_doc in self.equivalent_docstrings:
            for section in [
                Sections.SHORT_DESCRIPTION,
                Sections.LONG_DESCRIPTION,
                Sections.NOQAS,
            ]:
                g = google_doc.get_section(section)
                s = sphinx_doc.get_section(section)
                self.assertEqual(
                    g, s,
                    'Section {} differs for google and sphinx for "{}"'.format(
                        section,
                        google_doc.get_section(Sections.SHORT_DESCRIPTION),
                    ),
                )

    def test_get_types_equivalency(self):
        for google_doc, sphinx_doc in self.equivalent_docstrings:
            for section in [
                Sections.ARGUMENTS_SECTION,
                Sections.RETURNS_SECTION,
            ]:
                self.assertEqual(
                    google_doc.get_types(section),
                    sphinx_doc.get_types(section)
                )

    def test_get_items_equivalency(self):
        for google_doc, sphinx_doc in self.equivalent_docstrings:
            for section in [
                Sections.ARGUMENTS_SECTION,
                Sections.RAISES_SECTION,
                Sections.NOQAS,
            ]:
                self.assertEqual(
                    google_doc.get_items(section),
                    sphinx_doc.get_items(section),
                )

    def test_type_and_name_always_associated(self):
        """Make sure the type goes to the correct name."""
        names = ['x', 'y', 'a', 'z', 'q']
        types = ['int', 'float', 'Decimal', 'str', 'Any']
        short_description = 'A short docstring.'

        # Change the types of the parameters.
        shuffle(names)
        shuffle(types)

        sphinx_params = [
            ':param {}: An explanation'.format(name)
            for name in names
        ] + [
            ':type {}: {}'.format(name, _type)
            for name, _type in zip(names, types)
        ]
        shuffle(sphinx_params)
        sphinx_docstring = '\n'.join([
            short_description,
            '',
            '\n'.join(sphinx_params)
        ])

        google_params = [
            '    {} ({}): An explanation.'.format(name, _type)
            for name, _type in zip(names, types)
        ]
        google_docstring = '\n'.join([
            short_description,
            '',
            'Args:',
            '\n'.join(google_params),
        ])

        google_doc = Docstring.from_google(
            google.parse(Peaker(lex(google_docstring), 3))
        )
        sphinx_doc = Docstring.from_sphinx(
            sphinx.parse(Peaker(lex(sphinx_docstring), 2))
        )

        items = google_doc.get_items(Sections.ARGUMENTS_SECTION)
        self.assertTrue(
            items == sorted(items),
            'The items should be sorted.'
        )
        self.assertEqual(
            google_doc.get_items(Sections.ARGUMENTS_SECTION),
            sphinx_doc.get_items(Sections.ARGUMENTS_SECTION),
            'Google and Sphinx items should be the same.',
        )
        self.assertEqual(
            google_doc.get_types(Sections.ARGUMENTS_SECTION),
            sphinx_doc.get_types(Sections.ARGUMENTS_SECTION),
            'Google and Sphinx types should be the same.',
        )


class DocstringMethodTest(TestCase):
    """Tests for the Docstring class."""

    def test_global_noqa_no_body(self):
        """Ensure an empty noqa body means ignore everything."""
        root = google.parse(Peaker(lex('\n'.join([
            'A short explanation.',
            '',
            '    # noqa',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertTrue(docstring.ignore_all)

    def test_global_noqa_star_body(self):
        """Ensure noqa with * means ignore everything."""
        root = google.parse(Peaker(lex('\n'.join([
            'A short explanation.',
            '',
            '    # noqa: *',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertTrue(docstring.ignore_all)

    def test_get_short_description(self):
        """Ensure we can get the short description."""
        root = google.parse(
            Peaker(lex('Nothing but a short description.'), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.short_description,
            'Nothing but a short description.'
        )

    def test_get_long_description(self):
        """Make sure we can get the long description."""
        root = google.parse(Peaker(lex('\n'.join([
            'Ignore short.',
            '',
            'Long description should be contiguous.',
            '',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.long_description,
            'Long description should be contiguous.\n'
        )

    def test_get_arguments_description(self):
        """Make sure we can get the arguments description."""
        root = google.parse(Peaker(lex('\n'.join([
            'Something.',
            '',
            'Args:',
            '    x: An integer.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.arguments_description,
            'Args:\n    x: An integer.\n'
        )

    def test_get_argument_types(self):
        """Make sure we can get a dictionary of arguments to types."""
        root = google.parse(Peaker(lex('\n'.join([
            'Something.',
            '',
            'Args:',
            '    x (int): The first.',
            '    y (List[int], optional): The second.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        argtypes = docstring.get_argument_types()
        self.assertEqual(
            argtypes['x'],
            'int',
        )
        self.assertEqual(
            argtypes['y'],
            'List[int], optional',
        )

    def test_get_return_section(self):
        """Make sure we can get the returns description."""
        root = google.parse(Peaker(lex('\n'.join([
            'Ferment corn.',
            '',
            'Returns:',
            '    Bourbon.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.returns_description,
            'Returns:\n    Bourbon.\n',
        )

    def test_get_return_type(self):
        """Make sure we can get the return type described."""
        root = google.parse(Peaker(lex('\n'.join([
            'Ferment potato.',
            '',
            'Returns:',
            '    Alcohol: Vodka.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.get_return_type(),
            'Alcohol',
        )

    def test_get_yields_description(self):
        """Make sure we can get the yields description."""
        root = google.parse(Peaker(lex('\n'.join([
            'To pedestrians.',
            '',
            'Yields:',
            '    To pedestrians.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.yields_description,
            'Yields:\n    To pedestrians.\n',
        )

    def test_get_yields_type(self):
        """Make sure we can get the yields type."""
        root = google.parse(Peaker(lex('\n'.join([
            'Get slavic cats.',
            '',
            'Yields:',
            '    Cat: The slavic ones.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.get_yield_type(),
            'Cat',
        )

    def test_get_raises_description(self):
        """Make sure we can get the raises description."""
        root = google.parse(Peaker(lex('\n'.join([
            'Check if there\'s a problem.',
            '',
            'Raises:',
            '    ProblemException: if there is a problem.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.raises_description,
            'Raises:\n    ProblemException: if there is a problem.\n'
        )

    def test_get_exception_types(self):
        """Make sure we can get the types of exceptions raised."""
        root = google.parse(Peaker(lex('\n'.join([
            'Problematic.',
            '',
            'Raises:',
            '    IndexError: Frequently.',
            '    DoesNotExist: Always.',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.get_exception_types(),
            ['IndexError', 'DoesNotExist']
        )

    def test_get_noqas(self):
        """Make sure we can get all of the noqas in the docstring."""
        root = google.parse(Peaker(lex('\n'.join([
            'Full of noqas.',
            '',
            '# noqa: I200',
            '# noqa: I201 y',
            '',
            'Args:',
            '    x: Something. # noqa: I201',
            '\n',
        ])), lookahead=3))
        docstring = Docstring.from_google(root)
        self.assertEqual(
            docstring.get_noqas(),
            {
                'I200': [],
                'I201': ['x', 'y'],
            },
        )

    def test_has_section(self):
        """Make sure the docstring can tell if it has the given sections."""
        has_everything_root = google.parse(Peaker(lex('\n'.join([
            'Short decscription.',
            '',
            'Long description.',
            '',
            'Args:',
            '    x: Some value.',
            '',
            'Raises:',
            '    IntegrityError: Sometimes.',
            '',
            'Yields:',
            '    The occasional value.',
            '',
            'Returns:',
            '    When it completes.',
        ])), lookahead=3))
        docstring = Docstring.from_google(has_everything_root)
        self.assertTrue(all([
            docstring.has_short_description(),
            docstring.has_long_description(),
            docstring.has_args_section(),
            docstring.has_raises_section(),
            docstring.has_yields_section(),
            docstring.has_returns_section(),
        ]))
        has_only_short_description = google.parse(Peaker(lex('\n'.join([
            'Short description'
        ])), lookahead=3))
        docstring = Docstring.from_google(has_only_short_description)
        self.assertTrue(
            docstring.has_short_description(),
        )
        self.assertFalse(any([
            docstring.has_long_description(),
            docstring.has_args_section(),
            docstring.has_raises_section(),
            docstring.has_yields_section(),
            docstring.has_returns_section(),
        ]))


class DocstringForSphinxTests(TestCase):

    def test_has_everything_for_sphinx(self):
        has_everything_root = sphinx.parse(Peaker(lex('\n'.join([
            'Short decscription.',
            '',
            'Long description.',
            '',
            ':param x: Some value.',
            ':raises IntegrityError: Sometimes.',
            ':yields: The occasional value.',
            ':returns: When it completes.',
            ''
        ])), lookahead=3))
        docstring = Docstring.from_sphinx(has_everything_root)
        self.assertTrue(all([
            docstring.has_short_description(),
            docstring.has_long_description(),
            docstring.has_args_section(),
            docstring.has_raises_section(),
            docstring.has_yields_section(),
            docstring.has_returns_section(),
        ]))
        has_only_short_description = google.parse(Peaker(lex('\n'.join([
            'Short description'
        ])), lookahead=3))
        docstring = Docstring.from_google(has_only_short_description)
        self.assertTrue(
            docstring.has_short_description(),
        )
        self.assertFalse(any([
            docstring.has_long_description(),
            docstring.has_args_section(),
            docstring.has_raises_section(),
            docstring.has_yields_section(),
            docstring.has_returns_section(),
        ]))

    def test_get_argument_types(self):
        """Make sure we can get a dictionary of arguments to types."""
        root = sphinx.parse(Peaker(lex('\n'.join([
            'Something.',
            '',
            ':param x: The first.',
            ':param y: The second.',
            ':type x: int',
            ':type y: List[int], optional'
            '\n',
        ])), lookahead=3))
        from darglint.utils import generate_dot
        with open('_data/example.dot', 'w') as fout:
            fout.write(generate_dot(root))
        docstring = Docstring.from_sphinx(root)
        argtypes = docstring.get_argument_types()
        self.assertEqual(
            argtypes['x'],
            'int',
        )
        self.assertEqual(
            argtypes['y'],
            'List[int], optional',
        )
