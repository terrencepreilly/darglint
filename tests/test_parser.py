import ast
from unittest import TestCase, skip

from darglint.docstring import (
    Docstring,
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

    @skip('Allow this?')
    def test_doesnt_choke_on_missing_newline_for_returns(self):
        docstring = '\n'.join([
            'Serialize a label object.',
            '',
            'Returns: Valid JSON.',
        ])
        Docstring(docstring)

    def test_bare_noqa_can_be_parsed(self):
        docstring = '\n'.join([
            'The first line may have something, but others are missing.',
            '',
            '# noqa'
        ])
        Docstring(docstring)
