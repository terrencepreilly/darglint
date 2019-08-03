import ast
from collections import (
    defaultdict,
)
from unittest import TestCase, skip

from darglint.docstring.base import (
    Sections,
)
from darglint.docstring.google import (
    Docstring,
)
from darglint.lex import (
    condense,
    lex,
)
from darglint.node import (
    NodeType,
)
from darglint.parse.common import (
    ParserException,
    parse_colon,
    parse_keyword,
    parse_noqa,
    parse_word,
)
from darglint.parse.google import (
    parse,
    parse_item,
    parse_args,
    parse_compound_section,
    parse_description,
    parse_line,
    parse_line_with_type,
    parse_raises,
    parse_returns,
    parse_short_description,
    parse_simple_section,
    parse_type,
    parse_yields,
    KEYWORDS,
)
from darglint.parse.identifiers import (
    ArgumentIdentifier,
    ExceptionIdentifier,
)
from darglint.peaker import (
    Peaker
)
from darglint.parse.new_google import (
    parse as new_parse,
)
from darglint.errors import (
    IndentError,
)
from .utils import (
    replace,
    remove,
)


class DocstringTestCase(TestCase):

    # examples taken from
    # http://www.sphinx-doc.org/en/stable/ext/example_google.html

    def assertContains(self, tree, symbol):
        for child in tree.walk():
            if child.symbol == symbol:
                return
        self.fail('Tree does not contain symbol "{}"'.format(symbol))

    def values_of(self, tree, symbol):
        for child in tree.walk():
            if child.symbol == symbol and child.value is not None:
                yield child.value.value

    @replace('test_parse_noqa_for_argument_cyk')
    def test_parse_noqa_for_argument(self):
        """Make sure we can get the noqas."""
        func = '\n'.join([
            'def my_function():',
            '    """Has an extra argument, but thats okay.',
            '',
            '    Args:',
            '        arg1: This will be defined very soon.  # noqa: I102',
            '',
            '    """',
            '    print("Not done yet!")',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        self.assertTrue(doc.startswith('Has an extra'))
        docstring = Docstring(doc)
        self.assertTrue('arg1' in docstring.get_items(
            Sections.ARGUMENTS_SECTION)
        )
        noqas = docstring.get_noqas()
        self.assertTrue('arg1' in noqas['I102'])

    def test_parse_noqa_for_argument_cyk(self):
        func = '\n'.join([
            'def my_function():',
            '    """Has an extra argument, but thats okay.',
            '',
            '    Args:',
            '        arg1: This will be defined very soon.  # noqa: I102',
            '',
            '    """',
            '    print("Not done yet!")',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        self.assertTrue(doc.startswith('Has an extra'))
        node = new_parse(condense(lex(doc)))
        self.assertTrue(
            node.contains('noqa'),
        )
        maybe_noqa = None
        for child in node.walk():
            if child.symbol == 'noqa-maybe':
                maybe_noqa = child
                break
        word = None
        for child in maybe_noqa.walk():
            if child.symbol == 'words':
                word = child
                break
        self.assertEqual(
            word.value.value,
            'I102',
        )

    @replace('test_parse_noqa_for_global_cyk')
    def test_parse_noqa_for_global(self):
        """Make sure global targets are empty lists."""
        func = '\n'.join([
            'def my_function():',
            '    """Ignore missing return.',
            '',
            '    # noqa: I201',
            '',
            '    """',
            '    return "This is ignored."',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        docstring = Docstring(doc)
        noqas = docstring.get_noqas()
        self.assertEqual(
            noqas['I201'], [],
            'Expected target for I201 to be None but was {}'.format(
                noqas['I201']
            )
        )

    def test_parse_noqa_for_global_cyk(self):
        """Make sure global targets are empty lists."""
        func = '\n'.join([
            'def my_function():',
            '    """Ignore missing return.',
            '',
            '    # noqa: I201',
            '',
            '    """',
            '    return "This is ignored."',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        node = new_parse(condense(lex(doc)))
        self.assertTrue(node.contains('noqa'))

    @replace('test_parse_global_noqa_with_target_cyk')
    def test_parse_global_noqa_with_target(self):
        """Make sure targets are present in the lists."""
        func = '\n'.join([
            'def my_function(arg1):',
            '    """Ignore missing argument.',
            '',
            '    # noqa: I101 arg1',
            '',
            '    """',
            '    pass',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        docstring = Docstring(doc)
        noqas = docstring.get_noqas()
        self.assertTrue(
            'arg1' in noqas['I101']
        )

    def test_parse_global_noqa_with_target_cyk(self):
        """Make sure targets are present in the lists."""
        func = '\n'.join([
            'def my_function(arg1):',
            '    """Ignore missing argument.',
            '',
            '    # noqa: I101 arg1',
            '',
            '    """',
            '    pass',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        node = new_parse(condense(lex(doc)))
        self.assertTrue(node.contains('noqa'))

    @replace('test_parses_long_description_cyk')
    def test_parses_long_description(self):
        """Make sure we can parse the long description.

        The long description will include newlines.

        """
        func = '\n'.join([
            'def this_function_has_a_long_description(arg1):',
            '    """Return the arg, unchanged.',
            '',
            '    This function returns the arg, unchanged.  There is',
            '    no particular reason, but this is a good place to check to ',
            '    see that long descriptions are being parsed correctly. ',
            '    If they are, I\'m not sure why.  There is some magic ',
            '    going on here, in fact.',
            '',
            '    Args:',
            '        arg1: The value returned.',
            '',
            '    Returns:',
            '        The original argument, unchanged.',
            '',
            '    """',
            '    return arg1',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        docstring = Docstring(doc)
        long_description = docstring.get_section(Sections.LONG_DESCRIPTION)
        self.assertTrue(
            long_description.startswith('This function returns'),
            'Expected long description to start with "This function returns" '
            'but was {}'.format(repr(long_description[:20]))
        )

    def test_parses_long_description_cyk(self):
        func = '\n'.join([
            'def this_function_has_a_long_description(arg1):',
            '    """Return the arg, unchanged.',
            '',
            '    This function returns the arg, unchanged.  There is',
            '    no particular reason, but this is a good place to check to ',
            '    see that long descriptions are being parsed correctly. ',
            '    If they are, I\'m not sure why.  There is some magic ',
            '    going on here, in fact.',
            '',
            '    """',
            '    return arg1',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        tokens = list(lex(doc))
        node = new_parse(tokens)
        self.assertTrue(node is not None)

    def test_parse_long_description_multiple_sections(self):
        func = '\n'.join([
            'def this_function_has_multiple_long_descriptions():',
            '    """Do some math.',
            '',
            '    This is the first part of the long description.',
            '    it can be multiple lines, but doesn\'t have to be',
            '',
            '    This is the second half of the long description.',
            '',
            '    And the final part of it.',
            '',
            '    """',
            '    pass',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        tokens = list(lex(doc))
        node = new_parse(tokens)
        self.assertTrue(node is not None)

    @replace('test_arguments_can_by_extracted_cyk')
    def test_arguments_extracted_when_extant(self):
        """Make sure the arguments can be parsed."""
        docstring = '\n'.join([
            'Example function with types documented in the docstring.',
            '',
            '`PEP 484`_ type annotations are supported. If attribute, parameter, and',  # noqa: E501
            'return types are annotated according to `PEP 484`_, they do not need to be',  # noqa: E501
            'included in the docstring:',
            '',
            'Args:',
            '    param1 (int): The first parameter.',
            '    param2 (str): The second parameter.',
            '',
            'Returns:',
            '    bool: The return value. True for success, False otherwise.',
            '',
            '.. _PEP 484:',
            '    https://www.python.org/dev/peps/pep-0484/',
        ])
        doc = Docstring(docstring)

        args = doc.get_items(Sections.ARGUMENTS_SECTION)
        self.assertTrue('param1' in args)
        self.assertTrue('param2' in args)

    def test_arguments_can_be_extracted_cyk(self):
        docstring = '\n'.join([
            'Example function with types documented in the docstring.',
            '',
            '`PEP 484`_ type annotations are supported. If attribute, parameter, and',  # noqa: E501
            'return types are annotated according to `PEP 484`_, they do not need to be',  # noqa: E501
            'included in the docstring:',
            '',
            'Args:',
            '    param1 (int): The first parameter.',
            '    param2 (str): The second parameter.',
            '',
            'Returns:',
            '    bool: The return value. True for success, False otherwise.',
            '',
            '.. _PEP 484:',
            '    https://www.python.org/dev/peps/pep-0484/',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        args = list(self.values_of(tree, 'argument'))
        self.assertEqual(
            args,
            ['param1', 'param2'],
        )

    @replace('test_arguments_with_multiple_lines_cyk')
    def test_arguments_with_multiple_lines(self):
        """Make sure multiple lines are okay in items."""
        docstring = '\n'.join([
            'This is an example of a module level function.',
            '',
            'The format for a parameter is::',
            '',
            '    name (type): description',
            '        The description may span multiple lines. Following',
            '        lines should be indented. The "(type)" is optional.',
            '',
            '        Multiple paragraphs are supported in parameter',
            '        descriptions.',
            '',
            'Args:',
            '    param1 (int): The first parameter.',
            '    param2 (:obj:`str`, optional): The second parameter. Defaults to None.',  # noqa: E501
            '        Second line of description should be indented.',
            '    *args: Variable length argument list.',
            '    **kwargs: Arbitrary keyword arguments.',
            '',
            'Returns:',
            '    bool: True if successful, False otherwise.',
        ])
        doc = Docstring(docstring)
        args = doc.get_items(Sections.ARGUMENTS_SECTION)
        for arg in 'param1', 'param2', '*args', '**kwargs':
            self.assertTrue(arg in args)

    def test_crazy_argument_type_signatures(self):
        possible_types = [
            # '(int)',
            # '(:obj:`str`, optional)',
            '(:obj:`str`, optional)',
            '(:obj:`str`,\n    optional)',
        ]
        for type_ in possible_types:
            docstring = '\n'.join([
                'A short summary,',
                '',
                'Args:',
                '    x {}: y.'.format(type_),
            ])
            node = new_parse(condense(lex(docstring)))
            self.assertTrue(node.contains('type-section-parens'))

    def test_arguments_with_multiple_lines_cyk(self):
        docstring = '\n'.join([
            'This is an example of a module level function.',
            '',
            'The format for a parameter is::',
            '',
            '    name (type): description',
            '        The description may span multiple lines. Following',
            '        lines should be indented. The "(type)" is optional.',
            '',
            '        Multiple paragraphs are supported in parameter',
            '        descriptions.',
            '',
            'Args:',
            '    param1: The first parameter.',
            '    param2: The second parameter. Defaults to None.',  # noqa: E501
            '        Second line of description should be indented.',
            '    *args: Variable length argument list.',
            '    **kwargs: Arbitrary keyword arguments.',
            '',
            'Returns:',
            '    bool: True if successful, False otherwise.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'arguments-section')

    @remove
    @skip('Nested parentheses in type is invalid.')
    def test_arguments_are_last(self):
        """Make sure arguments can be parsed as the last section."""
        docstring = '\n'.join([
            'Example of docstring on the __init__ method.',
            '',
            'The __init__ method may be documented in either the class level',
            'docstring, or as a docstring on the __init__ method itself.',
            '',
            'Either form is acceptable, but the two should not be mixed. Choose one',  # noqa: E501
            'convention to document the __init__ method and be consistent with it.',  # noqa: E501
            '',
            'Note:',
            '    Do not include the `self` parameter in the ``Args`` section.',
            '',
            'Args:',
            '    param1 (str): Description of `param1`.',
            '    param2 (:obj:`int`, optional): Description of `param2`. Multiple',  # noqa: E501
            '        lines are supported.',
            '    param3 (list(str)): Description of `param3`.',
        ])
        doc = Docstring(docstring)
        args = doc.get_items(Sections.ARGUMENTS_SECTION)
        for arg in ['param1', 'param2', 'param3']:
            arg in args

    def test_arguments_are_last_cyk(self):
        """Make sure arguments can be parsed as the last section."""
        docstring = '\n'.join([
            'Example of docstring on the __init__ method.',
            '',
            'The __init__ method may be documented in either the class level',
            'docstring, or as a docstring on the __init__ method itself.',
            '',
            'Either form is acceptable, but the two should not be mixed. Choose one',  # noqa: E501
            'convention to document the __init__ method and be consistent with it.',  # noqa: E501
            '',
            'Note:',
            '    Do not include the `self` parameter in the ``Args`` section.',
            '',
            'Args:',
            '    param1: Description of `param1`.',
            '    param2: Description of `param2`. Multiple',  # noqa: E501
            '        lines are supported.',
            '    param3: Description of `param3`.',
        ])
        node = new_parse(condense(lex(docstring)))
        self.assertTrue(node.contains('arguments-section'))

    @replace('test_parse_yields_cyk')
    def test_can_parse_yields(self):
        """Make sure we can parse the yields section."""
        docstring = '\n'.join([
            'Some sort of short description.',
            '',
            'A longer description.',
            '',
            'Yields:',
            '    The number 5. Always.',
        ])
        doc = Docstring(docstring)
        self.assertTrue(len(doc.get_section(Sections.YIELDS_SECTION)) > 0)

    def test_parse_yields_cyk(self):
        tokens = condense(lex('\n'.join([
            'Some sort of short description.',
            '',
            'Yields:',
            '    The number 5. Always.',
        ])))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'yields-section')

    def test_parse_yields_with_type(self):
        tokens = condense(lex('\n'.join([
            'Short.',
            '',
            'Yields:',
            '    int: Some value.',
        ])))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'yields-type')

    def test_parse_yields_with_type_and_newline(self):
        tokens = condense(lex('\n'.join([
            'Short',
            '',
            'Yields:',
            '    int: Numbers that were calculated somehow.',
            '',
        ])))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'yields-type')

    @replace('test_parse_raises_cyk')
    def test_can_parse_raises(self):
        """Make sure we can parse the raises section."""
        docstring = '\n'.join([
            'This has a problem.',
            '',
            'Raises:',
            '    Exception: An exception for generic reasons.',
        ])
        doc = Docstring(docstring)
        self.assertTrue('Exception' in doc.get_section(
            Sections.RAISES_SECTION)
        )

    def test_parse_raises_cyk(self):
        docstring = '\n'.join([
            'This has a problem.',
            '',
            'Raises:',
            '    Exception: An exception for generic reasons.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'raises-section')
        self.assertContains(tree, 'exception')

    def test_parse_raises_multiple_lines(self):
        docstring = '\n'.join([
            'Iterates through the records.',
            '',
            'Args:',
            '    address: The address of the database.',
            '',
            'Raises:',
            '    StopIteration:  Once there are no more records,',
            '        or possible if there were never any records.',
            '    ConnectionError: If we were unable to establish a',
            '        connection.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        annotation_lookup = self.get_annotation_lookup(tree)
        values = {
            ExceptionIdentifier.extract(x)
            for x in annotation_lookup[ExceptionIdentifier]
        }
        self.assertEqual(
            values,
            {'StopIteration', 'ConnectionError'},
        )

    def test_parse_underindented_raises_section(self):
        docstring = '\n'.join([
            'Iterates through the records.',
            '',
            'Args:',
            '    address: The address of the database.',
            '',
            'Raises:',
            '    StopIteration:  Once there are no more records,',
            '    or possible if there were never any records.',
            '',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        annotation_lookup = self.get_annotation_lookup(tree)
        self.assertEqual(
            len(annotation_lookup[IndentError]),
            1
        )
        values = {
            ExceptionIdentifier.extract(x)
            for x in annotation_lookup[ExceptionIdentifier]
        }
        self.assertEqual(
            values,
            {'StopIteration'},
        )

    @replace('test_argument_types_can_be_parsed_cyk')
    def test_argument_types_can_be_parsed(self):
        docstring = '\n'.join([
            'This docstring contains types for its arguments.',
            '',
            'Args:',
            '    x (int): The first number.',
            '    y (float): The second number.',
        ])
        doc = Docstring(docstring)
        arg_types = {
            name: _type
            for name, _type in zip(
                doc.get_items(Sections.ARGUMENTS_SECTION),
                doc.get_types(Sections.ARGUMENTS_SECTION),
            )
        }
        self.assertEqual(arg_types['x'], 'int')
        self.assertEqual(arg_types['y'], 'float')

    def test_argument_types_can_be_parsed_cyk(self):
        docstring = '\n'.join([
            'This docstring contains types for its arguments.',
            '',
            'Args:',
            '    x (int): The first number.',
            '    y (float): The second number.',
        ])
        node = new_parse(condense(lex(docstring)))
        self.assertTrue(node.contains('arguments-section'))
        self.assertTrue(node.contains('type-section-parens'))

    @replace('test_can_parse_return_type_cyk')
    def test_can_parse_return_type(self):
        docstring = '\n'.join([
            'Return an approximation of pi.',
            '',
            'Returns:',
            '    Decimal: An approximation of pi.',
        ])
        doc = Docstring(docstring)
        self.assertEqual(doc.get_types(Sections.RETURNS_SECTION), 'Decimal')

    def test_can_parse_return_type_cyk(self):
        docstring = '\n'.join([
            'Return an approximation of pi.',
            '',
            'Returns:',
            '    Decimal: An approximation of pi.',
        ])
        node = new_parse(condense(lex(docstring)))
        self.assertTrue(node.contains('returns-section'))
        self.assertTrue(node.contains('returns-type'))

    @replace('test_parse_star_arguments_cyk')
    def test_star_arguments_parsed(self):
        docstring = '\n'.join([
            'Negate a function which returns a boolean.',
            '',
            'Args:',
            '    *fns (int): Functions which returns a boolean.',
            '',
            'Returns:',
            '    int: A function which returns fallse when any of the'
            '        callables return true, and true will all of the ',
            '        callables return false.',
        ])
        doc = Docstring(docstring)
        self.assertTrue('*fns' in doc.get_items(Sections.ARGUMENTS_SECTION))

    def test_parse_multiple_sections_cyk(self):
        sections = {
            'arguments-section': '\n'.join([
                'Args:',
                '    x: A number.',
                '    y: Another number, but with a much',
                '        longer description.',
            ]),
            'returns-section': '\n'.join([
                'Returns:',
                '    The description of the thing returned.',
                '    Can span multiple lines.',
            ]),
            'long-description': '\n'.join([
                'A long description can appear anywhere.'
            ]),
            'yields-section': '\n'.join([
                'Yields:',
                '    A bunch of numbers.',
            ])
        }
        keys = list(sections.keys())
        docstring = 'Some initial section.\n\n{}\n\n{}'
        for i in range(len(sections) - 1):
            for j in range(i + 1, len(sections)):
                section1 = sections[keys[i]]
                section2 = sections[keys[j]]
                tokens = condense(lex(docstring.format(section1, section2)))
                tree = new_parse(tokens)
                self.assertTrue(tree is not None)
                self.assertContains(tree, keys[i])
                self.assertContains(tree, keys[j])

    def test_parse_star_arguments_cyk(self):
        docstring = '\n'.join([
            'Negate a function which returns a boolean.',
            '',
            'Args:',
            '    *fns (int): Functions which returns a boolean.',
            '',
            'Returns:',
            '    int: A function which returns fallse when any of the'
            '        callables return true, and true will all of the ',
            '        callables return false.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'arguments')

    @replace('test_bare_noqa_can_be_parsed_cyk')
    def test_bare_noqa_can_be_parsed(self):
        docstring = '\n'.join([
            'The first line may have something, but others are missing.',
            '',
            '# noqa'
        ])
        Docstring(docstring)

    def test_bare_noqa_can_be_parsed_cyk(self):
        docstring = '\n'.join([
            'The first line may have something, but others are missing.',
            '',
            '# noqa'
        ])
        node = new_parse(condense(lex(docstring)))
        self.assertTrue(node.contains('noqa'))

    def test_nonhash_noqa_is_word(self):
        """Ensures we can distinguish a noqa from the word noqa."""
        docstring = '\n'.join([
            'The first line may have something, but others are missing.',
            '',
            'noqa'
        ])
        node = new_parse(condense(lex(docstring)))
        self.assertFalse(node.contains('noqa'))

    @remove
    def test_parse_keyword(self):
        """Make sure we can parse keywords."""
        for word, node_type in [
                ('Returns', NodeType.RETURNS),
                ('Args', NodeType.ARGUMENTS),
                ('Arguments', NodeType.ARGUMENTS),
                ('Yields', NodeType.YIELDS),
                ('Raises', NodeType.RAISES)
        ]:
            node = parse_keyword(Peaker(lex(word)), KEYWORDS)
            self.assertEqual(
                node.node_type,
                node_type
            )
            self.assertEqual(
                node.value,
                word,
            )

    @remove
    def test_parse_keyword_fails(self):
        """Make sure incorrectly calling the keyword parse fails."""
        for word in ['Not', 'a', 'keyword', 'args']:
            with self.assertRaises(ParserException):
                parse_keyword(Peaker(lex(word)), KEYWORDS)

    @remove
    def test_parse_colon(self):
        """Make sure we can parse colons."""
        node = parse_colon(Peaker(lex(':')))
        self.assertEqual(
            node.node_type, NodeType.COLON
        )

    @remove
    def test_parse_word(self):
        """Make sure we can parse a word."""
        node = parse_word(Peaker(lex('joHwI\'')))
        self.assertEqual(
            node.node_type,
            NodeType.WORD,
        )
        self.assertEqual(
            node.value,
            'joHwI\'',
        )

    @replace('test_parse_primitive_type_cyk')
    def test_parse_primitive_type(self):
        """Make sure we can parse a primitive type like int or str."""
        node = parse_type(Peaker(lex('(int)')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.children[1].value,
            'int',
        )

    def test_parse_primitive_type_cyk(self):
        docstring = '\n'.join([
            'Capitalize the given string.',
            '',
            'Args:',
            '    value (str): The string to capitalize.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'type-section-parens')

    @remove
    def test_type_cannot_by_empty(self):
        """Make sure that if we have a type it cannot be empty."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('()')))

    @replace('test_parse_compound_type_cyk')
    def test_parse_compound_type(self):
        """Make sure we can parse a type declaration with multiple items.

        These items should form a comma-separated list, and be enclosed in
        parentheses.

        """
        node = parse_type(Peaker(lex('(int, optional)')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.children[1].value,
            'int,',
        )
        self.assertEqual(
            node.children[2].value,
            'optional',
        )

    def test_parse_compound_type_cyk(self):
        docstring = '\n'.join([
            'Perform the given operation, if the item is present.',
            '',
            'Args:',
            '    fn (Callable): The function to call.',
            '    item (Any, Optional): The item, maybe.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'type-section-parens')

    @replace('test_parse_type_with_colon_in_arguments_cyk')
    def test_parse_type_with_colon(self):
        """Parse a type using the colon syntax."""
        node = parse_type(Peaker(lex('str:')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.children[0].value,
            'str',
        )

    def test_parse_type_with_colon_in_yields_cyk(self):
        docstring = '\n'.join([
            'Get the nodes in the tree.',
            '',
            'Yields:',
            '    Node: The nodes in the tree.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'yields-type')

    def test_parse_type_with_colon_in_returns_cyk(self):
        docstring = '\n'.join([
            'Get the nodes in the tree.',
            '',
            'Returns:',
            '    Iterable[Node]: The nodes in the tree,',
            '    in ascending order.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'returns-type')

    @remove
    def test_must_have_parentheses_around(self):
        """Make sure the type has to start with ( and end with )."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('(int')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('int)')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('( int (')))

    @replace('test_parse_type_with_line_continuation_cyk')
    def test_parse_type_with_line_continuation(self):
        """Make sure we allow for line continuation in types.

        See Issue 19.

        """
        # Should raise exception if not valid.  The ast module
        # handles line continuation in docstrings, surprisingly.
        # So, it just ends up looking like indents in random places.
        # Probably, indents shouldn't have been lexed except
        # immediately after newlines.
        parse_type(Peaker(lex(
            '(int, '
            '    str)'
        ), lookahead=2))

    def test_parse_type_with_line_continuation_cyk(self):
        """Make sure we allow for line continuation in types.

        See Issue 19.

        """
        # Should raise exception if not valid.  The ast module
        # handles line continuation in docstrings, surprisingly.
        # So, it just ends up looking like indents in random places.
        # Probably, indents shouldn't have been lexed except
        # immediately after newlines.
        docstring = '\n'.join([
            'Do something with complex array types.',
            '',
            'Args:',
            '    item (AVeryLongTypeDefinitionWhichMustBeSplit,',
            '       AcrossMultipleLines): Actually quite simple.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'type-section-parens')

    @remove
    def test_parse_line_without_indent(self):
        """Make sure lines don't need to have indents."""
        node = parse_line(Peaker(lex('word word\n')))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [NodeType.WORD, NodeType.WORD, NodeType.LINE],
        )

    @replace('test_parse_empty_line_cyk')
    def test_parse_empty_line(self):
        """Make sure we can parse a line with just an indent."""
        node = parse_line(Peaker(lex(' '*4 + '\n')))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [NodeType.INDENT, NodeType.LINE],
        )

    def test_parse_empty_line_cyk(self):
        """Make sure we can parse a line with just an indent."""
        node = new_parse(condense(lex(' '*4 + '\n')))
        self.assertTrue(node)

    @remove
    def test_parse_line_with_words(self):
        """Make sure we can parse a line with words."""
        node = parse_line(Peaker(lex(
            '    this is a line with words\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    @replace('test_parse_line_with_parentheses_cyk')
    def test_parse_line_with_parentheses(self):
        """Make sure lines can have parentheses in them."""
        node = parse_line(Peaker(lex(
            'This is a (parenthis-containing) line.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )

    def test_parse_line_with_parentheses_cyk(self):
        docstring = 'A short (description) with parentheses.'
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)

    @replace('test_parse_line_with_multiple_indents_cyk')
    def test_parse_line_with_multiple_indents(self):
        """Make sure code snippets are okay."""
        node = parse_line(Peaker(lex(
            '        word.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_line_with_multiple_indents_cyk(self):
        docstring = '\n'.join([
            'The short description.',
            '',
            '            The long description.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'long-description')

    @replace('test_parse_line_with_colons_cyk')
    def test_parse_line_with_colons(self):
        """Make sure lines with colons can be parsed."""
        node = parse_line(Peaker(lex(
            '    ::\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.COLON,
                NodeType.COLON,
                NodeType.LINE,
            ]
        )

    def test_parse_line_with_colons_cyk(self):
        """Make sure lines with colons can be parsed."""
        node = new_parse(condense(lex(
            '    ::\n'
        )))
        self.assertTrue(node)
        self.assertEqual(
            node.symbol,
            'long-description',
            'It can\'t be a short-description because of the indent.',
        )

    @replace('test_parse_line_which_looks_like_definition_cyk')
    def test_parse_line_which_looks_like_definition(self):
        """Make sure a line which looks like a definition can be parsed."""
        node = parse_line(Peaker(lex(
            '    Returns: Some value.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_line_which_looks_like_definition_cyk(self):
        """Make sure a line which looks like a definition can be parsed."""
        node = new_parse(condense(lex(
            '    Returns: Some value.\n'
        )))
        self.assertTrue(node)
        self.assertEqual(node.symbol, 'long-description')

    @remove
    def test_parse_returns_section(self):
        """Make sure can parse returns section."""
        node = parse_simple_section(Peaker(lex(
            'Returns:\n'
            '    A meaningful value.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    @replace('test_parse_line_with_type_cyk')
    def test_parse_line_with_type(self):
        """Make sure we can parse a line when it starts with a type."""
        node = parse_line_with_type(Peaker(lex(
            '    int: the square of something.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.TYPE,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_line_with_type_cyk(self):
        """Make sure we can parse a line when it starts with a type."""
        node = new_parse(condense(lex(
            '    int: the square of something.\n'
        )))
        self.assertTrue(node.contains('line'))

    @replace('test_parse_line_without_type_but_with_parentheses_cyk')
    def test_parse_line_without_type_but_with_parentheses(self):
        """Make sure we can have parentheses otherwise."""
        parse_line_with_type(Peaker(lex(
            '    A list of items (of type T), which pass the given test'
        )))

    def test_parse_line_without_type_but_with_parentheses_cyk(self):
        """Make sure we can have parentheses otherwise."""
        node = new_parse(condense(lex(
            '    A list of items (of type T), which pass the given test'
        )))
        self.assertTrue(node)

    @replace('test_parse_returns_section_with_type_cyk')
    def test_parse_returns_section_with_type(self):
        """Make sure the returns section can have a type."""
        node = parse_simple_section(Peaker(lex(
            'Returns:\n'
            '    int: The square of something.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.TYPE,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    def test_parse_returns_section_with_type_cyk(self):
        """Make sure the returns section can have a type."""
        node = new_parse(condense(lex(
            'Returns:\n'
            '    int: The square of something.\n'
            '\n'
        )))
        self.assertTrue(node)
        self.assertEqual(node.symbol, 'returns-section')

    @replace('test_parse_yields_section_cyk')
    def test_parse_yields_section(self):
        """Make sure we can parse a yields section."""
        node = parse_simple_section(Peaker(lex(
            'Yields:\n'
            '    Nodes in a stream.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.YIELDS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    def test_parse_yields_section_cyk(self):
        """Make sure we can parse a yields section."""
        node = new_parse(condense(lex(
            'Yields:\n'
            '    Nodes in a stream.\n'
            '\n'
        )))
        self.assertEqual(
            node.symbol,
            'yields-section',
        )

    @remove
    def test_parse_simple_section_cannot_start_with_args(self):
        """Make sure the simple section starts with return or yield."""
        with self.assertRaises(ParserException):
            parse_simple_section(Peaker(lex(
                'Args:\n'
                '    Not a simple section.\n'
                '\n'
            )))

    @remove
    def test_parse_item(self):
        """Make sure we can parse the parts of a compound section."""
        node = parse_item(Peaker(lex(
            '    x (int): The first number\n'
            '        to add\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.ITEM,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LPAREN,
                NodeType.WORD,
                NodeType.RPAREN,
                NodeType.TYPE,
                NodeType.ITEM_NAME,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.ITEM_DEFINITION,
                NodeType.ITEM,
            ]
        )

    @remove
    def test_parse_compound(self):
        """Make sure we can parse a compound section."""
        node = parse_compound_section(Peaker(lex('\n'.join([
            'Args:',
            '    x: X.',
            '    y: Y1.',
            '        Y2.',
            '    z (int, optional): Z.',
            '\n'
        ])), lookahead=3))
        self.assertEqual(node.node_type, NodeType.SECTION)
        body = node.children[1]
        self.assertEqual(
            body.node_type,
            NodeType.SECTION_COMPOUND_BODY,
        )
        self.assertEqual(
            len(body.children),
            3,
        )
        self.assertEqual(
            body.children[0].node_type,
            NodeType.ITEM,
        )

    @replace('test_parse_arguments_cyk')
    def test_parse_args(self):
        """Make sure we can parse an args section."""
        node = parse_args(Peaker(lex('\n'.join([
            'Args:',
            '    x: the item.',
            '\n',
        ])), lookahead=3))
        self.assertEqual(node.node_type, NodeType.ARGS_SECTION)

    def test_parse_arguments_cyk(self):
        docstring = '\n'.join([
            'Estimate the probability of being cool.',
            '',
            'Args:',
            '    hip: How hip it is.',
            '    hot: How hot it is.',
            '    coolness: Modified by this function.',
        ])
        tokens = condense(lex(docstring))
        tree = new_parse(tokens)
        self.assertTrue(tree is not None)
        self.assertContains(tree, 'arguments-section')
        self.assertContains(tree, 'argument')

    @remove
    def test_parse_raises(self):
        """Make sure we can parse the exceptions section."""
        node = parse_raises(Peaker(lex(
            'Raises:\n'
            '    ArrayIndexOutOfBounds: When the array index\n'
            '        is out of bounds.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.RAISES_SECTION,
        )

    @remove
    def test_parse_yields(self):
        node = parse_yields(Peaker(lex(
            'Yields:\n'
            '    The total amount of information.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.YIELDS_SECTION,
        )

    @replace('test_can_parse_returns_cyk')
    def test_parse_returns(self):
        node = parse_returns(Peaker(lex(
            'Returns:\n'
            '    A number of different\n'
            '    people, even species.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )

    def test_can_parse_returns_cyk(self):
        tokens = condense(lex('\n'.join([
            'This is the short description.',
            '',
            'Returns:',
            '    Lorem ipsum dolor.',
        ])))
        node = new_parse(tokens)
        self.assertTrue(node is not None)
        self.assertContains(node, 'returns-section')

    def test_can_have_word_returns_in_description(self):
        tokens = condense(lex('\n'.join([
            'Returns the sum of squares.'
        ])))
        node = new_parse(tokens)
        self.assertTrue(node is not None)

    def test_returns_section_can_be_multiple_indented_lines(self):
        tokens = condense(lex('\n'.join([
            'Returns the sum of squares.',
            '',
            'Returns:',
            '    The sum of squares:',
            '',
            '        SSx = \\sum(x - xbar)^2',
            '',
            '    For all x in X.',
        ])))
        node = new_parse(tokens)
        self.assertTrue(node is not None)
        self.assertContains(node, 'returns-section')

    @replace('test_parse_short_description_cyk')
    def test_parse_short_description(self):
        """Make sure we can parse the first line in the docstring."""
        node = parse_short_description(Peaker(lex(
            'This is a short description.\n'
        ), lookahead=3))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
            ] * 5 + [
                NodeType.SHORT_DESCRIPTION,
            ]
        )

    def test_parse_short_description_cyk(self):
        short_description = 'This is a short description.\n'
        tokens = list(lex(short_description))
        node = new_parse(tokens)
        self.assertTrue(node is not None)
        self.assertEqual(
            node.reconstruct_string(),
            short_description,
        )

    def test_short_description_can_be_without_newline(self):
        short_description = 'This is a short description.'
        tokens = list(lex(short_description))
        node = new_parse(tokens)
        self.assertTrue(node is not None)
        self.assertEqual(
            node.reconstruct_string(),
            short_description,
        )

    @replace('test_parse_whole_description_cyk')
    def test_parse_whole_description(self):
        """Make sure we can handle descriptions of multiple lines."""
        node = parse_description(Peaker(lex(
            'Short description\n'
            '\n'
            'Long : (description)\n'
            '\n'
            '    <code></code>\n'
            '\n'
        ), lookahead=3))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
                NodeType.WORD,
                NodeType.SHORT_DESCRIPTION,
                NodeType.WORD,
                NodeType.COLON,
                NodeType.LPAREN,
                NodeType.WORD,
                NodeType.RPAREN,
                NodeType.LINE,
                NodeType.LINE,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.LINE,
                NodeType.LONG_DESCRIPTION,
                NodeType.DESCRIPTION,
            ]
        )

    def test_parse_whole_description_cyk(self):
        """Make sure we can handle descriptions of multiple lines."""
        node = new_parse(condense(lex(
            'Short description\n'
            '\n'
            'Long : (description)\n'
            '\n'
            '    <code></code>\n'
            '\n'
        )))
        self.assertTrue(node)
        self.assertTrue(node.contains('short-description'))
        self.assertTrue(node.contains('long-description'))

    @replace('test_description_ends_with_sections_cyk')
    def test_description_ends_with_sections(self):
        """Make sure the description section doesn't eat everything."""
        peaker = Peaker(lex(
            'Short description.\n'
            '\n'
            'Long Description.\n'
            '\n'
            'Returns:\n'
            '    Nothing!\n'
            '\n'
        ), lookahead=3)
        parse_description(peaker)
        self.assertTrue(
            peaker.has_next()
        )
        node = parse_returns(peaker)
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )

    def test_description_ends_with_sections_cyk(self):
        """Make sure the description section doesn't eat everything."""
        node = new_parse(condense(lex(
            'Short description.\n'
            '\n'
            'Long Description.\n'
            '\n'
            'Returns:\n'
            '    Nothing!\n'
            '\n'
        )))
        self.assertTrue(node.contains('short-description'))
        self.assertTrue(node.contains('long-description'))
        self.assertTrue(node.contains('returns-section'))

    @replace('test_long_description_can_come_between_sections_cyk')
    def test_long_description_can_come_between_sections(self):
        """Make sure non-standard parts are treated as descriptions."""
        node = parse(Peaker(lex('\n'.join([
            'Double the number.',
            '',
            'Args:',
            '    x: The only argument..',
            '',
            'Requires:',
            '    Some kind of setup.',
            '',
        ])), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.DOCSTRING,
        )
        self.assertEqual(
            node.children[2].node_type,
            NodeType.LONG_DESCRIPTION,
        )

    def test_long_description_can_come_between_sections_cyk(self):
        """Make sure non-standard parts are treated as descriptions."""
        node = new_parse(condense(lex('\n'.join([
            'Double the number.',
            '',
            'Args:',
            '    x: The only argument..',
            '',
            'Requires:',
            '    Some kind of setup.',
            '',
        ]))))
        self.assertTrue(node.contains('long-description'))

    @replace('test_parse_all_section_types_cyk')
    def test_parses_all_section_types(self):
        """Make sure all section types can be parsed."""
        node = parse(Peaker(lex('\n'.join([
            'Short description.',
            '',
            'Long Description.',
            '',
            'Args:',
            '    x: The first argument with',
            '        two lines.',
            '    y: The second argument.',
            '',
            'Raises:',
            '    SomethingException: Randomly.',
            '',
            'Non-Standard:'
            '    Everything about this.',
            '',
            'Yields:',
            '    Values to analyze.',
        ])), lookahead=3))
        child_types = [x.node_type for x in node.children]
        self.assertEqual(
            child_types,
            [
                NodeType.DESCRIPTION,
                NodeType.ARGS_SECTION,
                NodeType.RAISES_SECTION,
                NodeType.LONG_DESCRIPTION,
                NodeType.YIELDS_SECTION,
            ]
        )

    def test_parse_all_section_types_cyk(self):
        """Make sure all section types can be parsed."""
        node = new_parse(condense(lex('\n'.join([
            'Short description.',
            '',
            'Long Description.',
            '',
            'Args:',
            '    x: The first argument with',
            '        two lines.',
            '    y: The second argument.',
            '',
            'Raises:',
            '    SomethingException: Randomly.',
            '',
            'Non-Standard:'
            '    Everything about this.',
            '',
            'Yields:',
            '    Values to analyze.',
        ]))))
        for symbol in [
            'short-description',
            'long-description',
            'arguments-section',
            'raises-section',
            'yields-section',
        ]:
            self.assertTrue(node.contains(symbol))

    @replace('test_parse_bare_noqa_statement_cyk')
    def test_parse_bare_noqa_statement(self):
        """Make sure we can parse noqa statements."""
        node = parse_noqa(Peaker(lex('# noqa\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.NOQA
            ]
        )

    def test_parse_bare_noqa_statement_cyk(self):
        """Make sure we can parse noqa statements."""
        node = new_parse(condense(lex('# noqa\n')))
        self.assertTrue(node.contains('noqa'))

    @replace('test_parse_noqa_with_target_cyk')
    def test_parse_noqa_with_target(self):
        """Make sure we can target a specific error message."""
        node = parse_noqa(Peaker(lex('# noqa: I203\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
            ],
        )

    def test_parse_noqa_with_target_cyk(self):
        """Make sure we can target a specific error message."""
        node = new_parse(condense(lex('# noqa: I203\n')))
        self.assertTrue(node.contains('noqa'))

    @replace('test_parse_noqa_with_target_and_argument_cyk')
    def test_parse_noqa_with_target_and_argument(self):
        """Make sure we can target specific args in a noqa."""
        node = parse_noqa(Peaker(lex('# noqa: I101 arg1, arg2\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LIST,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
            ]
        )

    def test_parse_noqa_with_target_and_argument_cyk(self):
        """Make sure we can target specific args in a noqa."""
        node = new_parse(condense(lex('# noqa: I101 arg1, arg2\n')))
        self.assertTrue(node.contains('noqa'))

    @replace('test_parse_inline_noqa_statements_cyk')
    def test_parse_inline_noqa_statements(self):
        """Make sure we can parse noqa statements."""
        node = parse_line(Peaker(lex('Something something.  # noqa: I201\n')))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
                NodeType.WORD,
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
                NodeType.LINE,
            ]
        )

    def test_parse_inline_noqa_statements_cyk(self):
        """Make sure we can parse noqa statements."""
        node = new_parse(condense(lex(
            'Something something.  # noqa: I201\n'
        )))
        self.assertTrue(node.contains('noqa'))

    @replace('test_only_indents_treated_as_newlines_in_compound_cyk')
    def test_only_indents_treated_as_newlines_in_compound(self):
        """Make sure that erroneous indentation is treated like newlines.

        This is okay to do, since other tools should pick up and handle
        erroneous newlines.  (Flake8, for example raises the W293 error.)

        """
        root = parse(Peaker(lex('\n'.join([
            'Maintains the heap invariant.',
            '',
            'Args:',
            '    heap: A something close to a heap.',
            '    ',
            'Returns:',
            '    That self-same heap.',
        ])), lookahead=3))
        self.assertTrue(
            root.first_instance(NodeType.RETURNS_SECTION) is not None,
            'The return section should not have been swallowed.',
        )

    def test_only_indents_treated_as_newlines_in_compound_cyk(self):
        """Make sure that erroneous indentation is treated like newlines.

        This is okay to do, since other tools should pick up and handle
        erroneous newlines.  (Flake8, for example raises the W293 error.)

        """
        node = new_parse(condense(lex('\n'.join([
            'Maintains the heap invariant.',
            '',
            'Args:',
            '    heap: A something close to a heap.',
            '    ',
            'Returns:',
            '    That self-same heap.',
        ]))))
        self.assertTrue(node.contains('returns-section'))

    @replace('test_only_indents_treated_newlines_within_simple_section_cyk')
    def test_only_indents_treated_newlines_within_simple_section(self):
        """Make sure indent-only lines are treated as newlines in simple."""
        root = parse(Peaker(lex('\n'.join([
            'Get the value of pi.',
            '',
            'Returns:',
            '    A value that is an approximation of pi.  This approximation',
            '    is actually just the quotient,',
            '    ',
            'Raises:',
            '    Exception: Seemingly at random.',
            '',
        ])), lookahead=3))
        raises = root.first_instance(NodeType.RAISES_SECTION)
        self.assertTrue(
            raises is not None,
        )

    def test_only_indents_treated_newlines_within_simple_section_cyk(self):
        """Make sure indent-only lines are treated as newlines in simple."""
        node = new_parse(condense(lex('\n'.join([
            'Get the value of pi.',
            '',
            'Returns:',
            '    A value that is an approximation of pi.  This approximation',
            '    is actually just the quotient,',
            '    ',
            'Raises:',
            '    Exception: Seemingly at random.',
        ]))))
        self.assertTrue(node.contains('raises-section'))

    @replace('test_parse_long_description_with_noqa_cyk')
    def test_parse_long_description_with_noqa(self):
        """Make sure noqas can appear in a global scope."""
        parse(Peaker(lex('\n'.join([
            'Short description can\'t have a noqa.'
            ''
            'But a long description can.'
            ''
            '# noqa: I101 arg1'
            '\n'
        ])), lookahead=3))

    def test_parse_long_description_with_noqa_cyk(self):
        """Make sure noqas can appear in a global scope."""
        node = new_parse(condense(lex('\n'.join([
            'Short description can\'t have a noqa.'
            ''
            'But a long description can.'
            ''
            '# noqa: I101 arg1'
            '\n'
        ]))))
        self.assertTrue(node.contains('noqa'))

    @replace('test_no_blank_line_swallows_sections')
    def test_parse_short_description_without_blank_line_raises_error(self):
        """Make sure there must be a blank line after the short description."""
        peaker = Peaker(lex('\n'.join([
            'Should not have a raises section.',
            'Args:',
            '    x: The divisor.',
            '    y: The dividend.',
            '',
        ])), lookahead=3)
        with self.assertRaises(ParserException):
            parse(peaker)

    def test_no_blank_line_swallows_sections(self):
        """Make sure there must be a blank line after the short description."""
        node = new_parse(condense(lex('\n'.join([
            'Should not have a raises section.',
            'Args:',
            '    x: The divisor.',
            '    y: The dividend.',
            '',
        ]))))
        self.assertFalse(
            node.contains('arguments-section'),
            'The arguments section should have been eaten -- that way the '
            'user gets a signal that they should separate the sections.'
        )

    def test_docstring_can_end_with_newlines(self):
        sections = {
            'arguments-section': '\n'.join([
                'Args:',
                '    x: y',
            ]),
            'returns-section': '\n'.join([
                'Returns:',
                '    Something.',
            ]),
            'yields-section': '\n'.join([
                'Yields:',
                '    Something.',
            ]),
            'raises-section': '\n'.join([
                'Raises:',
                '    Exception: In circumstances.',
            ]),
        }
        for key in sections:
            docstring = 'Short\n\n{}\n'.format(sections[key])
            node = new_parse(condense(lex(docstring)))
            self.assertTrue(
                node.contains(key),
                '{}:\n\n{}'.format(key, node)
            )

    def test_all_nodes_have_line_numbers(self):
        """Make sure all nodes in the AST have line numbers."""
        node = new_parse(condense(lex('\n'.join([
            'The short description should have line numbers.',
            '',
            'The long description should have line numbers.',
            '',
            'noqa: I203',
            '',
            'Args:',
            '    x (LineNumber, optional): The argument should have a',
            '        line number.',
            '',
            'Raises:',
            '    IndexError: The exception should have a line number.',
            '',
            'Yields:',
            '    LineNumber: The yields should have a line number.',
            '',
            'Returns:',
            '    LineNumber: The return section should have a line number.',
        ]))))
        for child in node.walk():
            self.assertTrue(
                node.line_numbers is not None,
                'The node {} does not have line numbers.'.format(
                    node,
                )
            )

    @replace('test_single_word_sections_parse_correctly_cyk')
    def test_single_word_sections_parse_correctly(self):
        """Make sure we can have a minimal amount of words in each section."""
        contents = '\n'.join([
            'def f(foo):',
            '    """foobar',
            '',
            '    Args:',
            '        foo: foobar',
            '',
            '    Returns:',
            '        bar',
            '',
            '    """',
            '    return "bar"',
        ])
        function = ast.parse(contents).body[0]
        docstring = ast.get_docstring(function)
        doc = Docstring(docstring)
        self.assertEqual(
            doc.get_section(Sections.SHORT_DESCRIPTION),
            'foobar',
        )
        self.assertEqual(
            doc.get_section(Sections.RETURNS_SECTION),
            'Returns:\n    bar',
        )
        self.assertEqual(
            doc.get_items(Sections.ARGUMENTS_SECTION),
            ['foo'],
        )

    def test_single_word_sections_parse_correctly_cyk(self):
        """Make sure we can have a minimal amount of words in each section."""
        contents = '\n'.join([
            'def f(foo):',
            '    """foobar',
            '',
            '    Args:',
            '        foo: foobar',
            '',
            '    Returns:',
            '        bar',
            '',
            '    """',
            '    return "bar"',
        ])
        function = ast.parse(contents).body[0]
        docstring = ast.get_docstring(function)
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('short-description'))
        self.assertTrue(node.contains('returns-section'))
        self.assertTrue(node.contains('arguments-section'))

    def test_type_with_multiple_words_multiple_lines(self):
        docstring = '\n'.join([
            'Test.',
            '',
            'Args:',
            '    input (:obj:`DataFrame <pandas.DataFrame>`, \\',
            '        :obj:`ndarray <numpy.ndarray>`, list): test',
        ])
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('arguments-section'))

    def test_type_can_have_indents(self):
        docstring = '\n'.join([
            'Test.',
            '',
            'Args:',
            '    input (a,       b): test',
            '',
            '# noqa: S001'
        ])
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('arguments-section'))

    def get_annotation_lookup(self, root):
        annotation_lookup = defaultdict(lambda: list())
        for child in root.walk():
            for annotation in child.annotations:
                annotation_lookup[annotation].append(child)
        return annotation_lookup

    def test_parse_sole_argument_with_two_lines(self):
        docstring = '\n'.join([
            'Short.',
            '',
            'Args:',
            '    x: Something something something.',
            '        Something something.',
            '        Something, something, something.',
            '',
            'Returns:',
            '    A value.',
        ])
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('arguments-section'))
        annotation_lookup = self.get_annotation_lookup(node)
        values = {
            ArgumentIdentifier.extract(x)
            for x in annotation_lookup[ArgumentIdentifier]
        }
        self.assertEqual(
            values,
            {'x'},
        )

    def test_parse_sole_argument_with_two_lines_indent_error(self):
        docstring = '\n'.join([
            'Short.',
            '',
            'Args:',
            '    x: Something something something.',
            '    Something something.',
            '    Something, something, something.',
            '',
            'Returns:',
            '    A value.',
        ])
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('arguments-section'))

    def test_parse_argument_with_two_lines(self):
        program = ('''
class _BaseError(object):
    def message(self, verbosity=1, raises=True):  # type: (int, bool) -> str
        """Get the message for this error, according to the verbosity.

        Args:
            verbosity: An integer in the set {1,2}, where 1 is a more
                terse message, and 2 includes a general description.
            raises: True if it should raise an exception.

        Raises:
            Exception: If the verbosity level is not recognized.

        Returns:
            An error message.

        """
        pass
''')
        docstring = ast.get_docstring(ast.parse(program).body[0].body[0])
        tokens = condense(lex(docstring))
        node = new_parse(tokens)
        self.assertTrue(node.contains('arguments-section'))
        annotation_lookup = self.get_annotation_lookup(node)
        self.assertEqual(len(annotation_lookup[ArgumentIdentifier]), 2)
        values = {
            ArgumentIdentifier.extract(x)
            for x in annotation_lookup[ArgumentIdentifier]
        }
        self.assertEqual(
            values,
            {'verbosity', 'raises'},
        )


class StyleWarningsTestCase(TestCase):
    """Tests for the new style warnings."""

    def assert_has_annotation(self, node, annotation):
        for child in node.walk():
            for a in child.annotations:
                if a == annotation:
                    return
        self.fail('Could not find annotation {}'.format(annotation.__name__))

    @skip('Finish me!')
    def test_excess_blank_lines_raise_style_error(self):
        """Ensure blank lines raise a style warning.

        This should only be an issue for excess lines between
        sections, or at the end of a docstring.

        """
        self.fail('Finish me!')

    @skip('Finish me!')
    def test_missing_line_between_sections_doesnt_kill_parser(self):
        """Make sure conjoined sections raises a style warning only."""
        self.fail('Finish me!')

    @skip('Finish me!')
    def test_missing_colon_after_section_raises_warning(self):
        """Make sure that a missing colon is just a style warning.

        This should only apply for docstrings where the given word
        is the only one which can result in a correct section.
        (Or it otherwise has the highest score when parsing.)

        """
        self.fail('Finish me!')

    @skip('Finish me!')
    def test_missing_colon_after_nonsection_doesnt_raise_warning(self):
        """Make sure that a non-section doesn't raise a style warning.

        If the section already exists, or another word like this one
        with a higher scoring parse, then this word shouldn't raise
        a syntax warning.

        """
        self.fail('Finish me!')
