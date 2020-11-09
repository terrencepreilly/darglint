import ast
from unittest import (
    TestCase,
)
from darglint.analysis.return_visitor import (
    ReturnVisitor,
)
from .utils import (
    reindent,
)


class ReturnsVisitorTests(TestCase):

    def assertFound(self, program):
        """Assert that the return was found.

        Args:
            program: The program to run the analysis on.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = ReturnVisitor()
        visitor.visit(function)
        self.assertTrue(visitor.returns)
        return visitor

    def _extract_type_name(self, node):
        if node is None:
            return None
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            ret = node.value.id
            ret += '['
            ret += ', '.join([
                self._extract_type_name(x) for x in node.slice.value.elts
            ])
            ret += ']'
            return ret

    def assertTypeFound(self, program, *args):
        function = ast.parse(reindent(program)).body[0]
        visitor = ReturnVisitor()
        visitor.visit(function)
        self.assertTrue(visitor.returns)
        actual = map(self._extract_type_name, visitor.return_types)
        self.assertEqual(list(actual), list(args))
        return visitor

    def assertNoneFound(self, program):
        """Assert that no return was found.

        Args:
            program: The program to run the analysis on.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
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

    def test_no_return_type(self):
        program = r'''
            def f():
                return 3
        '''
        self.assertTypeFound(program, None)

    def test_has_return_type(self):
        program = r'''
            def f() -> int:
                return 3
        '''
        self.assertTypeFound(program, 'int')

    def test_nested_with_return_types_sometimes(self):
        program = r'''
            def f(x):
                def g(y: int) -> int:
                    return y * 2
                return g(x)
        '''
        self.assertTypeFound(program, None, 'int')

    def test_nested_with_only_one_return_and_type(self):
        program = r'''
            def f(x):
                def g() -> int:
                    try:
                        x.something()
                    except:
                        return 2
                    return 0
                if g():
                    print('failed', file=sys.stderr)
        '''
        self.assertTypeFound(program, None, 'int')

    def test_compound_return(self):
        program = r'''
            def f() -> Tuple[int, int]:
                return (0, 1)
        '''
        self.assertTypeFound(program, 'Tuple[int, int]')

    def test_return_types_with_async_func(self):
        program = r'''
            async def f() -> int:
                return 3
        '''
        self.assertTypeFound(program, 'int')
