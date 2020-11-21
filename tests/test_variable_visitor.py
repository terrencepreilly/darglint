import ast
from unittest import (
    TestCase,
)

from darglint.analysis.variable_visitor import (
    VariableVisitor,
)

from .utils import (
    reindent,
)


class VariableVisitorTests(TestCase):

    def assertFound(self, program, *variables):
        """Assert that the return was found.

        Args:
            program: The program to run the analysis on.
            variables: The variables which we expect to have found
                (or empty, if we expect none.)

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program)).body[0]
        visitor = VariableVisitor()
        visitor.visit(function)
        self.assertEqual(sorted({
            x.id for x in visitor.variables
        }), sorted(variables))
        return visitor

    def test_no_variables(self):
        program = '''
            def f(x):
                return x * 2
        '''
        self.assertFound(program)

    def test_one_variables(self):
        program = '''
            def f(x):
                y = x * 2
                return y
        '''
        self.assertFound(program, 'y')

    def test_many_variables(self):
        program = '''
            def f(x):
                y = 2 * x
                pi = 3.1415
                something = 'cat'
                return something * int(y * pi)
        '''
        self.assertFound(program, 'y', 'pi', 'something')

    def test_no_variables_in_method(self):
        program = '''
            class X:
                def f(self, x):
                    self.x = x * 2
                    return self.x
        '''
        self.assertFound(program)

    def test_one_variable_in_method(self):
        program = '''
            class X:
                def f(self, x):
                    y = x * 2
                    self.x = y
                    return y
        '''
        self.assertFound(program, 'y')

    def test_many_variables_in_method(self):
        program = '''
            class X:
                def f(self, x):
                    y = 2 * x
                    pi = 3.1415
                    something = 'cat'
                    self.msg = something * int(y * pi)
                    return self.msg
        '''
        self.assertFound(program, 'y', 'pi', 'something')
