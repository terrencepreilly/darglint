import ast
from unittest import TestCase

from darglint.analysis.docstring_visitor import DocstringVisitor

from .utils import reindent


class DocstringVisitorTests(TestCase):

    def assertFound(self, program, *args):
        """Assert that the given docstrings were found.

        Args:
            program: The program to run the analysis on.
            args: The docstrings we expect to find.  If none,
                then this is an empty list.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = DocstringVisitor()
        visitor.visit(function)
        self.assertEqual(sorted(visitor.docstrings), sorted(args))
        return visitor

    def test_no_docstring(self):
        program = r'''
            def f(x):
                return x * 2
        '''
        self.assertFound(program)

    def test_single_docstring(self):
        docstring = 'Doubles'
        program = r'''
            def f(x):
                """{}"""
                return x * 2
        '''.format(docstring)
        self.assertFound(program, docstring)

    def test_method_docstring(self):
        docstring = 'Doubles'
        program = r'''
            class A:
                def f(self, x):
                    """{}"""
                    return x * self.quantity
        '''.format(docstring)
        self.assertFound(program, docstring)

    def test_doesnt_pick_up_early_string(self):
        program = r'''
            def f(x):
                return 'Not a docstring'
        '''
        self.assertFound(program)

    def test_expression_without_return_not_docstring(self):
        program = r'''
            def f(x):
                x + 2
        '''
        self.assertFound(program)

    def test_async_function_with_docstring(self):
        docstring = 'Documents.'
        program = r'''
            async def document(x):
                """{}"""
                raise NotImplementedError()
        '''.format(docstring)
        self.assertFound(program, docstring)
