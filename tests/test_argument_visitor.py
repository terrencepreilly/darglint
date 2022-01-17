import ast

from darglint.analysis.argument_visitor import (
    ArgumentVisitor,
)

from darglint.utils import (
    AnnotationsUtils,
)

from .utils import (
    reindent,
    require_python,
    TestCase,
)



class ArgumentVisitorTests(TestCase):

    def assertFound(self, program, *args):
        """Assert that the given arguments were found.

        Args:
            program: The program to run the analysis on.
            args: The arguments we expect to find.  If none,
                then this is an empty list.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = ArgumentVisitor()
        visitor.visit(function)
        self.assertEqual(sorted(visitor.arguments), sorted(args))
        return visitor

    def assertTypesFound(self, program, *types):
        function = ast.parse(reindent(program)).body[0]
        visitor = ArgumentVisitor()
        visitor.visit(function)
        AnnotationsUtils.assertEqual_annotations_and_types(visitor.annotations, types)
        return visitor

    def test_no_arguments(self):
        program = '''
            def f():
                return 3
        '''
        self.assertFound(program)

    def test_one_argument(self):
        program = '''
            def f(x):
                return x * 2
        '''
        self.assertFound(program, 'x')

    def test_many_arguments(self):
        program = '''
            def f(a, b, c, d, e, f):
                return a + b + c + d + e + f
        '''
        self.assertFound(
            program,
            'a', 'b', 'c', 'd', 'e', 'f',
        )

    def test_keyword_arguments(self):
        program = '''
            def f(x = 3, y = "hello"):
                return y * x
        '''
        self.assertFound(
            program,
            'x', 'y',
        )

    def test_keyword_only_arguments(self):
        program = '''
            def f(x, y, *, z):
                return "{}: {}".format(x * y, z)
        '''
        self.assertFound(
            program,
            'x', 'y', 'z'
        )

    @require_python(3, 8)
    def test_order_only_arguments(self):
        program = '''
            def f(x, y, /, z):
                return f'{x * y}: {z}'
        '''
        self.assertFound(
            program,
            'x', 'y', 'z'
        )

    @require_python(3, 8)
    def test_order_and_keyword_arguments(self):
        program = '''
            def f(x, y, /, z, *, q):
                return x + y + z + q
        '''
        self.assertFound(
            program,
            'x', 'y', 'z', 'q'
        )

    def test_method(self):
        program = '''
            class A(object):
                def f(self):
                    return  "hello"
        '''
        self.assertFound(program, 'self')

    def test_argument_type_inline(self):
        program = '''
            def f(x: int) -> float:
                return x * 0.5
        '''
        self.assertTypesFound(program, 'int')

    def test_argument_complicated_type_inline(self):
        program = '''
            def f(x: {}) -> float:
                return x * 0.5
        '''.format(self.complicated_type_hint)
        self.assertTypesFound(program, self.complicated_type_hint)

    def test_no_argument_type(self):
        program = '''
            def f(x) -> str:
                return "{}'s".format(x)
        '''
        self.assertTypesFound(program, None)

    def test_multiple_types_ordered(self):
        program = '''
            def f(x: int, y: str) -> str:
                return y * x
        '''
        self.assertTypesFound(program, 'int', 'str')

    def test_multiple_complicated_types_ordered(self):
        program = '''
            def f(x: {}, y: str) -> str:
                return y * x
        '''.format(self.complicated_type_hint)
        self.assertTypesFound(program, self.complicated_type_hint, 'str')
