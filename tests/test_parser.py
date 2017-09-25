from unittest import TestCase

from darglint.lex import lex
from darglint.parse import parse_arguments


class ParserTestCase(TestCase):
    # examples taken from
    # http://www.sphinx-doc.org/en/stable/ext/example_google.html

    def test_arguments_extracted_when_extant(self):
        docstring = """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: The return value. True for success, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/
    """
        docstring = '"""{}"""'.format(docstring)
        args = parse_arguments(lex(docstring))
        self.assertTrue('param1' in args)
        self.assertTrue('param2' in args)

    def test_arguments_with_multiple_lines(self):
        docstring = """This is an example of a module level function.

    The format for a parameter is::

        name (type): description
            The description may span multiple lines. Following
            lines should be indented. The "(type)" is optional.

            Multiple paragraphs are supported in parameter
            descriptions.

    Args:
        param1 (int): The first parameter.
        param2 (:obj:`str`, optional): The second parameter. Defaults to None.
            Second line of description should be indented.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bool: True if successful, False otherwise.
    """
        docstring = '"""{}"""'.format(docstring)
        args = parse_arguments(lex(docstring))
        self.assertEqual(args, {'param1', 'param2', '*args', '**kwargs'})

    def test_arguments_are_last(self):
        docstring = """Example of docstring on the __init__ method.

        The __init__ method may be documented in either the class level
        docstring, or as a docstring on the __init__ method itself.

        Either form is acceptable, but the two should not be mixed. Choose one
        convention to document the __init__ method and be consistent with it.

        Note:
            Do not include the `self` parameter in the ``Args`` section.

        Args:
            param1 (str): Description of `param1`.
            param2 (:obj:`int`, optional): Description of `param2`. Multiple
                lines are supported.
            param3 (list(str)): Description of `param3`.

        """
        docstring = '"""{}"""'.format(docstring)
        args = parse_arguments(lex(docstring))
        self.assertEqual(args, {'param1', 'param2', 'param3'})
