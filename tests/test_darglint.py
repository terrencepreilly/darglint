from unittest import TestCase
from darglint.darglint import get_ast, get_functions_and_docstrings


class GetFunctionsAndDocstrings(TestCase):

    def test_gets_functions(self):
        program = '''
def top_level_function(arg):
    """My docstring"""
    return 1
'''
        ast = get_ast(program)
        name, args, has_return, docstring = (
            get_functions_and_docstrings(ast)[0]
        )
        self.assertEqual(name, 'top_level_function')
        self.assertEqual(args, ['arg'])
        self.assertEqual(has_return, True)
        self.assertEqual(docstring, '"""My docstring"""')

    def test_gets_methods(self):
        program = '''
class MyClass(object):
    """Not this one"""

    def my_method(self, arg1, arg2):
        """But this one."""
        return arg1 - arg2
'''
        ast = get_ast(program)
        name, args, has_return, docstring = (
            get_functions_and_docstrings(ast)[0]
        )
        self.assertEqual(name, 'my_method')
        self.assertEqual(args, ['arg1', 'arg2'])
        self.assertEqual(has_return, True)
        self.assertEqual(docstring, '"""But this one."""')

    def test_removes_cls_from_class_arguments(self):
        program = '''
class AStaticClass(object):

    @classmethod
    def my_class_method(cls, arg1):
        """This is a class method."""
        print('Hey!')
'''
        ast = get_ast(program)
        name, args, has_return, docstring = (
            get_functions_and_docstrings(ast)[0]
        )
        self.assertEqual(args, ['arg1'])

    def test_tells_if_not_fruitful(self):
        program = '''
def baren_function(arg):
    print('hey!')
'''
        ast = get_ast(program)
        name, args, has_return, docstring = (
            get_functions_and_docstrings(ast)[0]
        )
        self.assertFalse(has_return)

    def test_no_docstring_is_okay(self):
        program = '''
def undocumented_function():
    return 3.1415
'''
        ast = get_ast(program)
        name, args, has_return, docstring = (
            get_functions_and_docstrings(ast)[0]
        )
        self.assertEqual(docstring, None)
