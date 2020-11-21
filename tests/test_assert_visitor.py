import ast
from unittest import TestCase

from darglint.analysis.assert_visitor import AssertVisitor

from .utils import reindent



class AssertVisitorTests(TestCase):

    def assertFound(self, program, n=0):
        tree = ast.parse(reindent(program))
        visitor = AssertVisitor()
        visitor.visit(tree)
        self.assertEqual(
            len(visitor.asserts),
            n,
            'Expected to encounter {} asserts, but encountered {}'.format(
                n,
                len(visitor.asserts),
            )
        )

    def test_no_asserts(self):
        program = r'''
            def f(x):
                return x * 2
        '''
        self.assertFound(program)

    def test_one_assertion(self):
        program = r'''
            def f(x):
                assert isinstance(x, int), "Expected an integer."
                return x * 2
        '''
        self.assertFound(program, 1)

    def test_two_assertions(self):
        program = r'''
            def f(x):
                assert isinstance(x, int), "Expected an integer."
                assert x > 0, "Expected a positive, non-zero integer."
                return 1 / x
        '''
        self.assertFound(program, 2)

    def test_assertion_in_async_func(self):
        program = r'''
            async def guaranteed(x):
                assert x
                return x
        '''
        self.assertFound(program, 1)
