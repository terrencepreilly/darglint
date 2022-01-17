import ast

from darglint.function_description import get_function_descriptions
from darglint.utils import AnnotationsUtils

from .utils import TestCase, reindent, require_python


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

    def test_qualified_error_from_library(self):
        program = '\n'.join([
            'async def error_middleware(overrides: Mapping[int, _Handler], request: web.Request,',
            '        handler: _Handler) -> web.Response:',
            '    """Use custom handlers for error conditions.',
            '',
            '    Raises:',
            '        aiohttp.web.HTTPException: Reraises any HTTPExceptions we don\'t have an override for.',
            '    """',
            '    try:',
            '        return await handler(request)',
            '    except aiohttp.web.HTTPException as e:',
            '        override = overrides.get(e.status)',
            '        if override is not None:',
            '            return await override(request)',
            '        raise',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.raises, {'aiohttp.web.HTTPException'})

    def test_implicit_error_caught_and_raised(self):
        program = '\n'.join([
            'def parse(value):',
            '    try:',
            '        default_parser.parse(value)',
            '    except ParserError:',
            '        logger.log("Default parser failed.")',
            '        raise',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.raises, {'ParserError'})

    def test_extracts_type_hints_for_arguments(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, ['int'])

    def test_extracts_complicated_type_hints_for_arguments(self):
        program = '\n'.join([
            'def square_root(x: {}) -> float:'.format(self.complicated_type_hint),
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, [self.complicated_type_hint])

    def test_argument_types_are_non_if_not_specified(self):
        program = '\n'.join([
            'def square_root(x):',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, [None])

    def test_extracts_return_type(self):
        program = '\n'.join([
            'def square_root(x: int) -> float:',
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.return_type, 'float')

    def test_extracts_complicated_return_type(self):
        program = '\n'.join([
            'def square_root(x: int) -> {}:'.format(self.complicated_type_hint),
            '    return x ** 0.5',
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        # TODO: change test with :
        # AnnotationsUtils.assertEqual_annotations_and_types(function.return_type, [self.complicated_type_hint])
        self.assertNotEqual(function.return_type, self.complicated_type_hint)

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
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, [None, None, None])

    def test_keyword_only_arguments_with_type_hints(self):
        program = '\n'.join([
            'def random_function(*, a: int, key: bool=True):'
            '   pass'
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['a', 'key'])
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, ['int', 'bool'])

    def test_keyword_only_arguments_with_complicated_type_hints(self):
        program = '\n'.join([
            'def random_function(*, a: {}, key: bool=True):'.format(self.complicated_type_hint),
            '   pass'
        ])
        tree = ast.parse(program)
        function = get_function_descriptions(tree)[0]
        self.assertEqual(function.argument_names, ['a', 'key'])
        AnnotationsUtils.assertEqual_annotations_and_types(function.argument_annotations, [self.complicated_type_hint, 'bool'])

    def test_has_assert(self):
        asserting_programs = [
            '\n'.join([
                'def f():',
                '    assert False, "Always fail."',
            ]),
            '\n'.join([
                'def f():',
                '    if True:',
                '        assert False, "Always fail."',
            ]),
            '\n'.join([
                'def f():',
                '    with open("/dev/null", "rb") as fin:',
                '        if "thevoid" in fin.read():',
                '            assert False, "Never fail."',
            ]),
        ]
        nonasserting_programs = [
            '\n'.join([
                'def f():',
                '    return "hey"',
            ]),
            '\n'.join([
                'def f():',
                '    if x < 10:',
                '        global x',
                '        x += 1',
            ]),
            '\n'.join([
                'def f():',
                '    with open("/dev/null", "rb") as fin:',
                '        if "thevoid" in fin.read():',
                '            return True',
            ]),
        ]
        for program in asserting_programs:
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertTrue(
                function.raises_assert,
            )
        for program in nonasserting_programs:
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertFalse(
                function.raises_assert,
            )

    @require_python(3, 8)
    def test_positional_arguments_token_ignored(self):
        programs = [
            '\n'.join([
                'def f(a, b, /):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a, /, b):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a, b=2, /):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a, /, b=2):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a: int, b: int, /):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a: int, /, b: int = 2):',
                '    return a * b',
            ]),
        ]
        for program in programs:
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertEqual(
                function.argument_names,
                ['a', 'b'],
                'Failed for program:\n\n```\n{}\n```\n'.format(
                    program,
                ),
            )

    def test_keyword_only_arguments_token_ignored(self):
        programs = [
            '\n'.join([
                'def f(*, a, b):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a, *, b):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(*, a, b=2):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(*, a=1, b=2):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(*, a: int, b: int):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(a: int, *, b: int):',
                '    return a * b',
            ]),
            '\n'.join([
                'def f(*, a: int, b: int = 2):',
                '    return a * b',
            ]),
        ]
        for program in programs:
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertEqual(
                function.argument_names,
                ['a', 'b'],
                'Failed for program:\n\n```\n{}\n```\n'.format(
                    program,
                ),
            )

    @require_python(3, 8)
    def test_positional_and_keyword_only_token_ignored(self):
        programs = [
            '\n'.join([
                'def f(a, /, b, *, c):',
                '    return a * b * c',
            ]),
            '\n'.join([
                'def f(a, /, *, b, c):',
                '    return a * b * c',
            ]),
            '\n'.join([
                'def f(a, /, b=2, *, c=5):',
                '    return a * b * c',
            ]),
            '\n'.join([
                'def f(a: int, /, *, b: int, c: float):',
                '    return a * b * c',
            ]),
        ]
        for program in programs:
            tree = ast.parse(program)
            function = get_function_descriptions(tree)[0]
            self.assertEqual(
                function.argument_names,
                ['a', 'b', 'c'],
                'Failed for program:\n\n```\n{}\n```\n'.format(
                    program,
                ),
            )

    def test_nested_functions_partition_signatures(self):
        program = reindent(r'''
            def f(x):
                """Always raise an exception from another function."""
                def g(y):
                    """Always raise an exception."""
                    raise Exception('Always fail')
                return g(y)
        ''')
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        self.assertEqual(
            len(functions),
            2,
        )
        outer_function = [x for x in functions if x.name == 'f'][0]
        inner_function = [x for x in functions if x.name == 'g'][0]
        self.assertEqual(
            outer_function.argument_names,
            ['x'],
        )
        self.assertTrue(
            outer_function.has_return,
        )
        self.assertEqual(
            outer_function.raises,
            set(),
        )
        self.assertEqual(
            inner_function.argument_names,
            ['y'],
        )
        self.assertEqual(
            inner_function.raises,
            {'Exception'},
        )
        self.assertFalse(
            inner_function.has_return,
        )

    def test_lambda_doesnt_alter_signature(self):
        program = reindent(r'''
            def f():
                get_message = lambda x: '{}!'.format(x)
                print(get_message(7))
        ''')
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        self.assertEqual(
            len(functions),
            1,
        )
        function = functions[0]
        self.assertEqual(
            function.argument_names,
            [],
        )

    def test_property(self):
        program = reindent(r'''
            class A:
                @property
                def f() -> int:
                    return 3
        ''')
        tree = ast.parse(program)
        functions = get_function_descriptions(tree)
        self.assertEqual(
            len(functions),
            1,
        )
        function = functions[0]
        self.assertTrue(function.is_property)
