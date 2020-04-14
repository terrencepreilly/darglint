import ast
from unittest import TestCase
from darglint.function_description import get_function_descriptions


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
            '    @name.setter',
            '    def name(self, value):',
            '        pass',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['value'])

    def test_tells_if_not_fruitful(self):
        program = '\n'.join([
            'def baren_function(arg):',
            '    print(\'hey!\')',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertFalse(function.has_return)

    def test_doesnt_mistake_inner_function_return_for_fruitful(self):
        program = '\n'.join([
            'def baren_function(arg):',
            '   def get_pi():',
            '       return 3.14',
            '   if arg * get_pi < 30:',
            '       raise Exception("Bad multiplier!")',
        ])
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        for function in functions:
            if function.name == 'baren_function':
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

    def test_raise_with_fully_qualified_name(self):
        program = '\n'.join([
            'from rest_framework import serializers',
            'class ProblematicSerializer(serializers.Serializer):',
            '    def create(self, validated_data):',
            '        try:',
            '            validated_data["should be here"]',
            '        except Exception as e:',
            '            raise serializers.ValidationError(e)',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.raises, {'ValidationError'})

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

    def test_multiple_returns_has_returns(self):
        program = '\n'.join([
            'def check_module_installed(name):',
            '    try:',
            '        __import__(name)',
            '    except ImportError:',
            '        return False',
            '    else:',
            '        return True',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertTrue(function.has_return)

    def test_return_in_try_else(self):
        """Make sure we can have a return statement in any part of a try."""
        program_template = '\n'.join([
            'def check_module_installed(name):',
            '    try:',
            '        {}',
            '    except ImportError:',
            '        {}',
            '    else:',
            '        {}',
        ])
        for pattern in [
            ['pass', 'pass', 'return name'],
            ['pass', 'return name', 'pass'],
            ['return name', 'pass', 'pass'],
        ]:
            program = program_template.format(*pattern)
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertTrue(
                function.has_return,
                'Failed for \n{}'.format(program),
            )

    def test_keyword_only_arguments(self):
        """PEP 3102"""
        program = '\n'.join([
            'def random_function(a, b, *, key=None):'
            '   pass'
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['a', 'b', 'key'])
        self.assertEqual(function.argument_types, [None, None, None])

    def test_keyword_only_arguments_with_type_hints(self):
        program = '\n'.join([
            'def random_function(*, a: int, key: bool=True):'
            '   pass'
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['a', 'key'])
        self.assertEqual(function.argument_types, ['int', 'bool'])
