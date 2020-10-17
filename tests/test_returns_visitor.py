import ast
from unittest import (
    TestCase,
)
from darglint.analysis.return_visitor import (
    ReturnVisitor,
)


class ReturnsVisitorTests(TestCase):

    def _reindent(self, program):
        """Reindent the program.

        This makes it a little more natural for writing the
        program in a string.

        Args:
            program: A program which is indented too much.

        Returns:
            The program, reindented.

        """
        return '\n'.join([
            x[12:] for x in program.split('\n')
            if x[12:]
        ])

    def assertFound(self, program):
        """Assert that the return was found.

        Args:
            program: The program to run the analysis on.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(self._reindent(program)).body[0]
        visitor = ReturnVisitor()
        visitor.visit(function)
        self.assertTrue(visitor.returns)
        return visitor

    def assertNoneFound(self, program):
        """Assert that no return was found.

        Args:
            program: The program to run the analysis on.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(self._reindent(program)).body[0]
        visitor = ReturnVisitor()
        visitor.visit(function)
        self.assertEqual(visitor.returns, [])
        return visitor

    def test_no_return(self):
        program = r'''
            def f():
                pass
        '''
        self.assertNoneFound(program)

    def test_nested_no_return(self):
        program = r'''
            def f():
                def g():
                    pass
        '''
        self.assertNoneFound(program)

    def test_simplest_function(self):
        program = r'''
            def f():
                return 3
        '''
        self.assertFound(program)

    def test_early_return(self):
        program = r'''
            def f(x):
                if x < 0:
                    return -1
                for i in range(x):
                    if complex_condition(x, i):
                        return i
        '''
        self.assertFound(program)

    def test_conditional_return(self):
        program = r'''
            def f():
                if MY_GLOBAL:
                    return 1
                else:
                    return 2
        '''
        self.assertFound(program)

    def test_return_in_context(self):
        program = r'''
            def f():
                with open('/tmp/input', 'r') as fin:
                    return fin.readlines()
        '''
        self.assertFound(program)

    def test_returns_none(self):
        program = r'''
            def f():
                return
        '''
        visitor = self.assertFound(program)
        self.assertEqual(
            visitor.returns[0].value,
            None,
        )

    def test_returns_non_none(self):
        program = r'''
            def f():
                return 3
        '''
        visitor = self.assertFound(program)
        self.assertTrue(
            isinstance(visitor.returns[0].value, ast.AST),
        )
