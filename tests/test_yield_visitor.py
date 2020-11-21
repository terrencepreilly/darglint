import ast
from unittest import (
    TestCase,
)
from darglint.analysis.yield_visitor import (
    YieldVisitor,
)
from .utils import (
    reindent,
)


class YieldsVisitorTests(TestCase):

    def assertFound(self, program):
        """Assert that the yield was found.

        Args:
            program: The program to run the analysis on.

        Yields:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = YieldVisitor()
        visitor.visit(function)
        self.assertTrue(visitor.yields)
        return visitor

    def assertNoneFound(self, program):
        """Assert that no yield was found.

        Args:
            program: The program to run the analysis on.

        Yields:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = YieldVisitor()
        visitor.visit(function)
        self.assertEqual(visitor.yields, [])
        return visitor

    def test_no_yield(self):
        program = r'''
            def f():
                pass
        '''
        self.assertNoneFound(program)

    def test_nested_no_yield(self):
        program = r'''
            def f():
                def g():
                    pass
        '''
        self.assertNoneFound(program)

    def test_simplest_function(self):
        program = r'''
            def f():
                yield 3
        '''
        self.assertFound(program)

    def test_early_yield(self):
        program = r'''
            def f(x):
                if x < 0:
                    yield -1
                for i in range(x):
                    if complex_condition(x, i):
                        yield i
        '''
        self.assertFound(program)

    def test_conditional_yield(self):
        program = r'''
            def f():
                if MY_GLOBAL:
                    yield 1
                else:
                    yield 2
        '''
        self.assertFound(program)

    def test_yield_in_context(self):
        program = r'''
            def f():
                with open('/tmp/input', 'r') as fin:
                    yield fin.readlines()
        '''
        self.assertFound(program)

    def test_yields_none(self):
        program = r'''
            def f():
                yield
        '''
        visitor = self.assertFound(program)
        self.assertEqual(
            visitor.yields[0].value,
            None,
        )

    def test_yields_non_none(self):
        program = r'''
            def f():
                yield 3
        '''
        visitor = self.assertFound(program)
        self.assertTrue(
            isinstance(visitor.yields[0].value, ast.AST),
        )

    def test_yield_from(self):
        program = r'''
            def f():
                yield from (x for x in range(10))
        '''
        self.assertFound(program)
