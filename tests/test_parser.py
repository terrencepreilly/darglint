import ast
from unittest import TestCase, skip

from darglint.docstring.google import (
    Docstring,
)
from darglint.lex import (
    lex
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
from darglint.peaker import (
    Peaker
)


class DocstringTestCase(TestCase):

    # examples taken from
    # http://www.sphinx-doc.org/en/stable/ext/example_google.html

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
        self.assertTrue('arg1' in docstring.arguments_description)
        noqas = docstring.get_noqas()
        self.assertTrue('arg1' in noqas['I102'])

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
        self.assertTrue(
            docstring.long_description.startswith('This function returns'),
            'Expected long description to start with "This function returns" '
            'but was {}'.format(repr(docstring.long_description[:20]))
        )

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

        self.assertTrue('param1' in doc.arguments_description)
        self.assertTrue('param2' in doc.arguments_description)

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
        for arg in 'param1', 'param2', '*args', '**kwargs':
            self.assertTrue(arg in doc.arguments_description)

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
        for arg in ['param1', 'param2', 'param3']:
            self.assertTrue(arg in doc.arguments_description)

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
        self.assertTrue(len(doc.yields_description) > 0)

    def test_can_parse_raises(self):
        """Make sure we can parse the raises section."""
        docstring = '\n'.join([
            'This has a problem.',
            '',
            'Raises:',
            '    Exception: An exception for generic reasons.',
        ])
        doc = Docstring(docstring)
        self.assertTrue('Exception' in doc.raises_description)

    def test_argument_types_can_be_parsed(self):
        docstring = '\n'.join([
            'This docstring contains types for its arguments.',
            '',
            'Args:',
            '    x (int): The first number.',
            '    y (float): The second number.',
        ])
        doc = Docstring(docstring)
        arg_types = doc.get_argument_types()
        self.assertEqual(arg_types['x'], 'int')
        self.assertEqual(arg_types['y'], 'float')

    def test_can_parse_return_type(self):
        docstring = '\n'.join([
            'Return an approximation of pi.',
            '',
            'Returns:',
            '    Decimal: An approximation of pi.',
        ])
        doc = Docstring(docstring)
        self.assertEqual(doc.get_return_type(), 'Decimal')

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
        self.assertTrue('*fns' in doc.arguments_description)

    def test_bare_noqa_can_be_parsed(self):
        docstring = '\n'.join([
            'The first line may have something, but others are missing.',
            '',
            '# noqa'
        ])
        Docstring(docstring)

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

    def test_parse_keyword_fails(self):
        """Make sure incorrectly calling the keyword parse fails."""
        for word in ['Not', 'a', 'keyword', 'args']:
            with self.assertRaises(ParserException):
                parse_keyword(Peaker(lex(word)), KEYWORDS)

    def test_parse_colon(self):
        """Make sure we can parse colons."""
        node = parse_colon(Peaker(lex(':')))
        self.assertEqual(
            node.node_type, NodeType.COLON
        )

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

    def test_type_cannot_by_empty(self):
        """Make sure that if we have a type it cannot be empty."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('()')))

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

    def test_must_have_parentheses_around(self):
        """Make sure the type has to start with ( and end with )."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('(int')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('int)')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('( int (')))

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

    def test_parse_line_with_parentheses(self):
        """Make sure lines can have parentheses in them."""
        node = parse_line(Peaker(lex(
            'This is a (parenthis-containing) line.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )

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

    def test_parse_line_without_type_but_with_parentheses(self):
        """Make sure we can have parentheses otherwise."""
        parse_line_with_type(Peaker(lex(
            '    A list of items (of type T), which pass the given test'
        )))

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

    def test_parse_simple_section_cannot_start_with_args(self):
        """Make sure the simple section starts with return or yield."""
        with self.assertRaises(ParserException):
            parse_simple_section(Peaker(lex(
                'Args:\n'
                '    Not a simple section.\n'
                '\n'
            )))

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

    def test_parse_args(self):
        """Make sure we can parse an args section."""
        node = parse_args(Peaker(lex('\n'.join([
            'Args:',
            '    x: the item.',
            '\n',
        ])), lookahead=3))
        self.assertEqual(node.node_type, NodeType.ARGS_SECTION)

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

    def test_all_nodes_have_line_numbers(self):
        """Make sure all nodes in the AST have line numbers."""
        peaker = Peaker(lex('\n'.join([
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
        ])), lookahead=3)
        root = parse(peaker)
        for node in root.walk():
            self.assertTrue(
                node.line_numbers is not None,
                'The node ({}) {} does not have line numbers.'.format(
                    node.node_type,
                    node.value,
                )
            )
