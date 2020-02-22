import random
import string
from unittest import (
    TestCase,
    skip,
)
from darglint.docstring.base import (
    DocstringStyle,
)
from darglint.config import (
    Configuration,
    Strictness,
)
from darglint.lex import (
    condense,
    lex,
)
from darglint.parse.numpy import (
    parse,
)
from darglint.parse.identifiers import (
    ArgumentItemIdentifier,
    ArgumentTypeIdentifier,
    NoqaIdentifier,
)
from darglint.utils import (
    CykNodeUtils,
)


class NumpydocTests(TestCase):

    def setUp(self):
        self.config = Configuration(
            ignore=[],
            message_template=None,
            style=DocstringStyle.NUMPY,
            strictness=Strictness.FULL_DESCRIPTION,
        )

    def assertContains(self, docstring, node_name, msg=''):
        self.assertTrue(
            CykNodeUtils.contains(docstring, node_name),
            msg or 'Expected docstring to contain {} but it did not'.format(
                node_name,
            )
        )

    def assertIdentified(self, docstring, identifier, expected, msg=''):
        actual = {
            identifier.extract(x)
            for x in CykNodeUtils.get_annotated(
                docstring,
                identifier,
            )
        }
        self.assertEqual(
            expected, actual,
            msg or 'Expected identified {}, but found {}'.format(
                repr(expected), repr(actual)
            )
        )

    def assertHasIdentifier(self, docstring, identifier):
        self.assertTrue(len(
            CykNodeUtils.get_annotated(docstring, identifier)
        ) > 0)

    def test_can_parse_short_description(self):
        raw_docstring = '\n'.join([
            'The sum of two numbers.',
            '',
        ])
        tokens = condense(lex(raw_docstring, self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'short-description')

    @skip('Implement this?')
    def test_can_parse_deprecation_warning(self):
        raw_docstring = '\n'.join([
            'Multiply two numbers.',
            '',
            '.. deprecated:: 1.6.0',
            '    Nobody does this anymore!',
            '    This will be removed in NumPy 2.0.0',
            '',
        ])
        tokens = condense(lex(raw_docstring, self.config))
        docstring = parse(tokens)
        for node_name in [
            'deprecation-warning',
            'deprecation-version',
            'deprecation-description'
        ]:
            self.assertContains(
                docstring,
                node_name,
            )

    def test_can_parse_long_description(self):
        raw_docstring = '\n'.join([
            'Monkey things up.',
            '',
            'Not to be confused with sabotage.',
            '',
        ])
        tokens = condense(lex(raw_docstring, self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'long-description')

    def test_can_parse_empty_parameters_section(self):
        """Make sure we can parse an empty parameter section.

        The numpy format allows for unambiguous section headings,
        without necessarily having any content below them.
        We'll probably want to raise an error for an empty
        parameters section.

        """
        raw_docstring = '\n'.join([
            'Cry aloud.',
            '',
            'Parameters',
            '----------',
            '',
        ])
        tokens = condense(lex(raw_docstring, self.config))
        docstring = parse(tokens)
        for node_name in ['arguments-section']:
            self.assertContains(docstring, node_name)

    def test_header_can_have_variable_length(self):
        for underline in [
            '-' * x
            for x in range(1, 15)
        ]:
            raw_docstring = '\n'.join([
                'Cry aloud.',
                '',
                'Parameters',
                '{}',
                '',
            ]).format(underline)
            tokens = condense(lex(raw_docstring, self.config))
            docstring = parse(tokens)
            self.assertContains(docstring, 'arguments-section')

    def test_single_parameter(self):
        parameter_descriptions = [
            'Something.',
            'A slightly longer description which '
            'can contain a colon: yes.',
            'A description over\n    two lines.',
            'A description with two lines and newlines.\n\n'
            '    It\'s perfectly fine.',
        ]
        for parameter_description in parameter_descriptions:
            raw_docstring = '\n'.join([
                'Process some data.',
                '',
                'Parameters',
                '----------',
                'x',
                '    {}',
                '',
            ]).format(parameter_description)
            tokens = condense(lex(raw_docstring, self.config))
            docstring = parse(tokens)
            self.assertContains(
                docstring,
                'arguments-section',
                'Expected docstring with {} as item description '
                'but did not parse as arguments section'.format(
                    repr(parameter_description),
                )
            )
            self.assertIdentified(
                docstring,
                ArgumentItemIdentifier,
                {'x'},
            )

    def test_multiple_parameters(self):
        raw_docstring_pattern = '\n'.join([
              'Rename the items.',
              '',
              'Parameters',
              '----------',
              '{}',
              '',
        ])
        number = random.randint(2, 5)
        names = string.ascii_letters[:number]
        raw_docstring = raw_docstring_pattern.format(
            '\n'.join([
                '{}:\n    Something'.format(name)
                for name in names
            ])
        )
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'arguments-section')
        self.assertIdentified(docstring, ArgumentItemIdentifier, set(names))

    @skip('Not collecting whitespace yet')
    def test_error_associated_with_no_whitespace_before_type(self):
        self.fail('Finish me!')

    def test_arguments_section_with_types(self):
        raw_docstring = '\n'.join([
            'Turn the person into a Mr. Fontaine.',
            '',
            'Parameters',
            '----------',
            'x : Person',
            '    The person to fontainify.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertIdentified(docstring, ArgumentTypeIdentifier, {'Person'})

    def test_two_combined_parameters(self):
        raw_docstring = '\n'.join([
            'Get the cartesian product of two lists.',
            '',
            'Parameters',
            '----------',
            'x1, x2 : List[Any]',
            '    The lists to use for the product.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertIdentified(docstring, ArgumentItemIdentifier, {'x1, x2'})

    def test_returns_section(self):
        raw_docstring = '\n'.join([
            'Return the number two.',
            '',
            'Returns',
            '-------',
            '{2}',
            '    The number two.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'returns-section')

    @skip('Implement return type missing exception')
    def test_return_type_missing_exception(self):
        raw_docstring = '\n'.join([
            'Return the number three.',
            '',
            'Returns',
            '-------',
            'The number three.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'returns-section')
        # self.assertTrueHasIdentifier(docstring, ReturnTypeMissingException)

    @skip('implement return type identifier')
    def test_return_type_with_single_name(self):
        raw_docstring = '\n'.join([
            'Return the number four.',
            '',
            'Returns',
            '-------',
            'number : int',
            '    A number to use.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'returns-section')
        # self.assertIdentified(docstring, RetrunTypeIdentifier, {'int'})

    def test_return_type_with_multiple_names(self):
        raw_docstring = '\n'.join([
            'Return the number four.',
            '',
            'Returns',
            '-------',
            'number : int',
            '    A number to use.',
            'repr: str',
            '    The representation of the number.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'returns-section')
        # self.assertIdentified(
        #     docstring, RetrunTypeIdentifier, {'int', 'str'}
        # )

    def test_yields_section(self):
        raw_docstring = '\n'.join([
            'Yield the number two.',
            '',
            'Yields',
            '-------',
            '{2}',
            '    The number two.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'yields-section')

    @skip('Implement yield type missing exception')
    def test_yield_type_missing_exception(self):
        raw_docstring = '\n'.join([
            'Yield the number three.',
            '',
            'Yields',
            '-------',
            'The number three.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'yields-section')
        # self.assertTrueHasIdentifier(docstring, YieldTypeMissingException)

    @skip('implement yield type identifier')
    def test_yield_type_with_single_name(self):
        raw_docstring = '\n'.join([
            'Yield the number four.',
            '',
            'Yields',
            '-------',
            'number : int',
            '    A number to use.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'yields-section')
        # self.assertIdentified(docstring, RetrunTypeIdentifier, {'int'})

    def test_yield_type_with_multiple_names(self):
        raw_docstring = '\n'.join([
            'Yield the number four.',
            '',
            'Yields',
            '-------',
            'number : int',
            '    A number to use.',
            'repr: str',
            '    The representation of the number.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'yields-section')
        # self.assertIdentified(
        #     docstring, ReturnTypeIdentifier, {'int', 'str'}
        # )

    @skip('Implement the error!')
    def test_receives_without_yield_error(self):
        raw_docstring = '\n'.join([
            'Yield the number four.',
            '',
            'Receives',
            '-------',
            'repr_or_number : {REPR, NUMB}',
            '    Whether to yield a representation or number.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'yields-section')
        # self.assertHasIdentifier(
        #     docstring, ReceivesWithoutYieldException
        # )

    def test_receives_section(self):
        raw_docstring = '\n'.join([
            'Count up to the number.',
            '',
            'Receives',
            '--------',
            'maximum : int',
            '    The new maximum number.',
            '',
            'Yields',
            '------',
            'int',
            '    The next number up to the maximum.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'receives-section')

    def test_other_parameters_section(self):
        raw_docstring = '\n'.join([
            'Translate the string to the target language.',
            '',
            'Parameters',
            '----------',
            'x : str',
            '    The string to translate.',
            '',
            'Other Parameters',
            '----------------',
            'target : str',
            '    The target language.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'other-arguments-section')
        self.assertIdentified(
            docstring,
            ArgumentItemIdentifier,
            {'x', 'target'},
        )

    def test_raises_section(self):
        raw_docstring = '\n'.join([
            'Always fail.',
            '',
            'Raises',
            '------',
            'Exception',
            '    Under all conditions.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'raises-section')

    def test_multiple_entries_in_raises(self):
        raw_docstring = '\n'.join([
                'A problematic function.',
                '',
                'Raises',
                '------',
                'InvalidNumberException',
                '    An exception for if it\'s '
                '        invalid.',
                'Exception',
                '    Seemingly at random.',
                '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'raises-section')

    def test_warns_section(self):
        raw_docstring = '\n'.join([
            'Always warn.',
            '',
            'Warns',
            '-----',
            'Warning',
            '    Under all conditions.',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertContains(docstring, 'warns-section')

    def test_noqas_in_long_description(self):
        raw_docstring = '\n'.join([
            'Sore snork stort stort.',
            '',
            '# noqa: DAR101',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertIdentified(
            docstring,
            NoqaIdentifier,
            {'DAR101'},
        )

    def test_noqas_in_parameters_section(self):
        raw_docstring = '\n'.join([
            'Get the cartesian product of two lists.',
            '',
            'Parameters',
            '----------',
            'x1 : List[Any]',
            '    The lists to use for the product. # noqa: DAR101',
            '',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertIdentified(
            docstring,
            NoqaIdentifier,
            {'DAR101'},
        )

    def test_noqas_in_short_description(self):
        raw_docstring = '\n'.join([
            'Gave gambol grubble goince # noqa: *',
        ])
        tokens = condense(lex(raw_docstring, config=self.config))
        docstring = parse(tokens)
        self.assertIdentified(
            docstring,
            NoqaIdentifier,
            {'*'},
        )
