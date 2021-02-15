import ast
from unittest import (
    TestCase,
)

from darglint.analysis.function_and_method_visitor import (
    FunctionAndMethodVisitor,
)

from .utils import (
    reindent,
)


class FunctionAndMethodVisitorTests(TestCase):

    def parse_and_visit(self, program):
        """Parse a program and visit it with the visitor.

        Args:
            program: The program to run the analysis on.

        Returns:
            The visitor
        """
        function = ast.parse(reindent(program))
        visitor = FunctionAndMethodVisitor()
        visitor.visit(function)
        return visitor

    def assertFoundMethods(self, program, *args):
        """Assert that the given methods were found.

        Args:
            program: The program to run the analysis on.
            args: The names of the methods we expect to have found.
                If there are none, then this is an empty list.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        visitor = self.parse_and_visit(program)
        self.assertEqual(sorted({
            method.name for method in visitor.methods
        }), sorted(args))
        return visitor

    def assertFoundFunctions(self, program, *args):
        """Assert that the given functions were found.

        Args:
            program: The program to run the analysis on.
            args: The names of the functions we expect to have found.
                If there are none, then this is an empty list.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        visitor = self.parse_and_visit(program)
        self.assertEqual(sorted({
            function.name for function in visitor.functions
        }), sorted(args))
        return visitor

    def assertFoundProperties(self, program, *args):
        """Assert that the given functions were found.

        Args:
            program: The program to run the analysis on.
            args: The names of the properties we expect to have found.
                If there are none, then this is an empty list.

        Returns:
            The visitor, in case you want to do more analysis.

        """
        visitor = self.parse_and_visit(program)
        self.assertEqual(sorted({
            function.name for function in visitor.properties
        }), sorted(args))
        return visitor

    def test_no_methods_or_functions(self):
        program = '''
            print("Hello, world!")
        '''
        self.assertFoundFunctions(program)
        self.assertFoundMethods(program)
        self.assertFoundProperties(program)

    def test_functions_found(self):
        program = '''
            def double(x):
                return x * 2

            def halve(x):
                return x / 2
        '''
        self.assertFoundFunctions(program, 'double', 'halve')
        self.assertFoundMethods(program)
        self.assertFoundProperties(program)

    def test_methods_found(self):
        program = '''
            class Ops(object):

                def _my_inner_method(self, op):
                    self.op = op

                def apply(self, *values):
                    return self.op(*values)
        '''
        self.assertFoundFunctions(program)
        self.assertFoundMethods(program, '_my_inner_method', 'apply')
        self.assertFoundProperties(program)

    def test_properties_found(self):
        program = '''
            class Ops(object):

                @property
                def a(self):
                    return "a"
                
                @property
                def b(self):
                    return "b"
        '''
        self.assertFoundFunctions(program)
        self.assertFoundMethods(program)
        self.assertFoundProperties(program, "a", "b")

    def test_nested_functions_found(self):
        program = '''
            def log_arguments(func):
                def _inner(*args, **kwargs):
                    get_logger().info('{} {}'.format(args, kwargs))
                    return func(*args, **kwargs)
                return _inner
        '''
        self.assertFoundFunctions(program, 'log_arguments', '_inner')
        self.assertFoundMethods(program)
        self.assertFoundProperties(program)

    def test_functions_nested_in_method(self):
        program = '''
            class X:
                def x(self, value):
                    def f():
                        return value * MY_GLOBAL
                    print(f())
        '''
        self.assertFoundFunctions(program, 'f')
        self.assertFoundMethods(program, 'x')
        self.assertFoundProperties(program)

    def test_methods_nested_in_function(self):
        program = '''
            def f(language):
                class Translator(BaseTranslator):

                    def __init__(self):
                        super(Translator, self).__init__()
                        self.language = language

                    def translate(self, word):
                        return self.dictionary[self.language][word]

                return Translator
        '''
        self.assertFoundFunctions(program, 'f')
        self.assertFoundMethods(program, '__init__', 'translate')
        self.assertFoundProperties(program)

    def test_properties_nested_in_function(self):
        program = '''
            def f(language):
                class Translator(BaseTranslator):

                    def __init__(self):
                        super(Translator, self).__init__()
                        self.language = language
                    
                    @property
                    def language(self, word):
                        return "English"

                return Translator
        '''
        self.assertFoundFunctions(program, 'f')
        self.assertFoundMethods(program, '__init__')
        self.assertFoundProperties(program, "language")

    def test_lambdas_not_functions(self):
        program = '''
            x = lambda y: y * 2
            print(x(3))
        '''
        self.assertFoundFunctions(program)
        self.assertFoundMethods(program)
        self.assertFoundProperties(program)
