import ast
from unittest import TestCase
from darglint.darglint import get_function_descriptions


class GetFunctionsAndDocstrings(TestCase):

    def test_gets_functions(self):
        program = '\n'.join([
            'def top_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.name, 'top_level_function')
        self.assertEqual(function.argument_names, ['arg'])
        self.assertEqual(function.has_return, True)
        self.assertEqual(function.docstring, 'My docstring')

    def test_gets_methods(self):
        program = '\n'.join([
            'class MyClass(object):',
            '    """Not this one"""',
            '',
            '    def my_method(self, arg1, arg2):',
            '        """But this one."""',
            '        return arg1 - arg2',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.name, 'my_method')
        self.assertEqual(function.argument_names, ['arg1', 'arg2'])
        self.assertEqual(function.has_return, True)
        self.assertEqual(function.docstring, 'But this one.')

    def test_removes_cls_from_class_arguments(self):
        program = '\n'.join([
            'class AStaticClass(object):',
            '',
            '    @classmethod',
            '    def my_class_method(cls, arg1):',
            '        """This is a class method."""',
            '        print(\'Hey!\')',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['arg1'])

    def test_setters_and_getters_treated_like_normal_methods(self):
        program = '\n'.join([
            'class SomeClass(object):',
            '',
            '    @property',
            '    def name(self):',
            '        return "Gerald"',
            '',
            '    @name.setter',
            '    def name(self, value):',
            '        pass',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[1]
        self.assertEqual(function.argument_names, ['value'])

    def test_tells_if_not_fruitful(self):
        program = '\n'.join([
            'def baren_function(arg):',
            '    print(\'hey!\')',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertFalse(function.has_return)

    def test_no_docstring_is_okay(self):
        program = '\n'.join([
            'def undocumented_function():',
            '    return 3.1415',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.docstring, None)

    def test_tells_if_raises_errors(self):
        program = '\n'.join([
            'def errorful_function():',
            '   raise ZeroDivisionError',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.raises, {'ZeroDivisionError'})

    def test_extracts_type_hints_for_arguments(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_types, ['int'])

    def test_argument_types_are_non_if_not_specified(self):
        program = '\n'.join([
            'def square_root(x):',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_types, [None])

    def test_extracts_return_type(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.return_type, 'float')

    def test_return_type_non_if_not_specified(self):
        program = '\n'.join([
            'def square_root(x):',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.return_type, None)

    def test_star_arguments_retain_stars(self):
        program = '\n'.join([
            'def xsum(*nums: List[int]) -> int:',
            '    return sum(nums)'
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['*nums'])
