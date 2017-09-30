import ast
from unittest import TestCase
from darglint.darglint import get_function_descriptions


class GetFunctionsAndDocstrings(TestCase):

    def test_gets_functions(self):
        program = '''
def top_level_function(arg):
    """My docstring"""
    return 1
'''
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.name, 'top_level_function')
        self.assertEqual(function.argument_names, ['arg'])
        self.assertEqual(function.has_return, True)
        self.assertEqual(function.docstring, 'My docstring')

    def test_gets_methods(self):
        program = '''
class MyClass(object):
    """Not this one"""

    def my_method(self, arg1, arg2):
        """But this one."""
        return arg1 - arg2
'''
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.name, 'my_method')
        self.assertEqual(function.argument_names, ['arg1', 'arg2'])
        self.assertEqual(function.has_return, True)
        self.assertEqual(function.docstring, 'But this one.')

    def test_removes_cls_from_class_arguments(self):
        program = '''
class AStaticClass(object):

    @classmethod
    def my_class_method(cls, arg1):
        """This is a class method."""
        print('Hey!')
'''
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['arg1'])

    def test_tells_if_not_fruitful(self):
        program = '''
def baren_function(arg):
    print('hey!')
'''
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertFalse(function.has_return)

    def test_no_docstring_is_okay(self):
        program = '''
def undocumented_function():
    return 3.1415
'''
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.docstring, None)
