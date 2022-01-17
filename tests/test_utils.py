import ast

from darglint.utils import AnnotationsUtils, AstNodeUtils

from .utils import TestCase, reindent


class AstNodeUtilsTest(TestCase):
    # parse
    def test_parse_error(self):
        program = '\n'.join([
            'deftop_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        self.assertIsNone(AstNodeUtils.parse(program))

    def test_parse_ok(self):
        program = '\n'.join([
            'def top_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        parsed = AstNodeUtils.parse(program)
        self.assertIsNotNone(parsed)
        self.assertIsInstance(parsed, ast.Module)
        self.assertEqual(parsed.body[0].name, 'top_level_function')

    def test_parse_type_hint(self):
        program = '\n'.join([
            'int',
        ])
        parsed = AstNodeUtils.parse(program)
        self.assertIsNotNone(parsed)
        self.assertIsInstance(parsed, ast.Module)
        self.assertEqual(parsed.body[0].value.id, 'int')

    def test_parse_complicated_type_hint(self):
        program = '\n'.join([
            self.complicated_type_hint,
        ])
        parsed = AstNodeUtils.parse(program)
        self.assertIsNotNone(parsed)
        self.assertIsInstance(parsed, ast.Module)
        self.assertEqual(ast.dump(parsed.body[0]), ast.dump(ast.parse(self.complicated_type_hint).body[0]))

    # dump
    def test_dump_None(self):
        program = None
        self.assertIsNone(AstNodeUtils.dump(program))

    def test_dump_None_list(self):
        program = [None]
        dumped = AstNodeUtils.dump(program)
        self.assertIsInstance(dumped, list)
        self.assertIsNone(dumped[0])

    def test_dump_function(self):
        program = '\n'.join([
            'def top_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump(parsed.body[0])
        self.assertEqual(dumped, ast.dump(parsed.body[0], annotate_fields=False))

    def test_dump_function_list(self):
        program = '\n'.join([
            'def top_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump([parsed.body[0]])
        self.assertIsInstance(dumped, list)
        self.assertEqual(dumped[0], ast.dump(parsed.body[0], annotate_fields=False))

    def test_dump_type(self):
        program = '\n'.join([
            'int',
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump(parsed.body[0])
        self.assertEqual(dumped, ast.dump(parsed.body[0], annotate_fields=False))

    def test_dump_type_list(self):
        program = '\n'.join([
            'int',
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump([parsed.body[0]])
        self.assertIsInstance(dumped, list)
        self.assertEqual(dumped[0], ast.dump(parsed.body[0], annotate_fields=False))

    def test_dump_complicated_type(self):
        program = '\n'.join([
            self.complicated_type_hint,
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump(parsed.body[0])
        self.assertEqual(dumped, ast.dump(parsed.body[0], annotate_fields=False))

    def test_dump_complicated_type_list(self):
        program = '\n'.join([
            self.complicated_type_hint,
        ])
        parsed = ast.parse(program)
        dumped = AstNodeUtils.dump([parsed.body[0]])
        self.assertIsInstance(dumped, list)
        self.assertEqual(dumped[0], ast.dump(parsed.body[0], annotate_fields=False))

    def test_compare_two_nodes(self):
        program = '\n'.join([
            self.complicated_type_hint,
        ])

        parsed = ast.parse(program)
        dumped = AstNodeUtils.compare_two_nodes(parsed, parsed)
        self.assertTrue(AstNodeUtils.compare_two_nodes(parsed, parsed))

class AnnotationsUtilsTest(TestCase):
    def test_parse_annotation_or_types_none(self):
        program = None
        self.assertIsNone(AnnotationsUtils.parse_annotation_or_types(program))

    def test_parse_annotation_or_types_error_syntax(self):
        program = '\n'.join([
            'deftop_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        self.assertIsNone(AnnotationsUtils.parse_annotation_or_types(program))

    def test_parse_annotation_or_types_error_syntax(self):
        program = '\n'.join([
            'deftop_level_function(arg):',
            '    """My docstring"""',
            '    return 1',
        ])
        self.assertIsNone(AnnotationsUtils.parse_annotation_or_types(program))

    def test_parse_annotation_or_types_nothing(self):
        program = ''
        self.assertIsNone(AnnotationsUtils.parse_annotation_or_types(program))

    def test_parse_annotation_or_types_simple(self):
        program = 'int'
        self.assertEqual(ast.dump(ast.parse(program).body[0].value), ast.dump(AnnotationsUtils.parse_annotation_or_types(program)))

    def test_parse_annotation_or_types_complicated(self):
        program = self.complicated_type_hint
        self.assertEqual(ast.dump(ast.parse(program).body[0].value), ast.dump(AnnotationsUtils.parse_annotation_or_types(program)))

    def test_parse_annotation_or_types_simple_bad(self):
        program = 'int'
        self.assertNotEqual(ast.dump(ast.parse('str').body[0].value), ast.dump(AnnotationsUtils.parse_annotation_or_types(program)))

    def test_parse_annotation_or_types_complicated_bad(self):
        program = self.complicated_type_hint
        self.assertNotEqual(ast.dump(ast.parse('str').body[0].value), ast.dump(AnnotationsUtils.parse_annotation_or_types(program)))

    # parse_types
    def test_parse_types_simple(self):
        program = 'int'
        self.assertEqual([ast.dump(ast.parse(program).body[0].value)]*2, list(map(ast.dump,AnnotationsUtils.parse_types([program,program]))))

    def test_parse_types_complicated(self):
        program = self.complicated_type_hint
        self.assertEqual([ast.dump(ast.parse(program).body[0].value)]*2, list(map(ast.dump,AnnotationsUtils.parse_types([program,program]))))

    def test_parse_types_simple_bad(self):
        program = 'int'
        self.assertNotEqual([ast.dump(ast.parse('str').body[0].value)]*2, list(map(ast.dump,AnnotationsUtils.parse_types([program,program]))))

    def test_parse_types_complicated_bad(self):
        program = self.complicated_type_hint
        self.assertNotEqual([ast.dump(ast.parse('str').body[0].value)]*2, list(map(ast.dump,AnnotationsUtils.parse_types([program,program]))))


    # parse_types_and_dump

    def test_parse_types_and_dump_simple(self):
        program = 'int'
        self.assertEqual([ast.dump(ast.parse(program).body[0].value, annotate_fields=False)]*2, AnnotationsUtils.parse_types_and_dump([program,program]))

    def test_parse_types_and_dump_complicated(self):
        program = self.complicated_type_hint
        self.assertEqual([ast.dump(ast.parse(program).body[0].value, annotate_fields=False)]*2, AnnotationsUtils.parse_types_and_dump([program,program]))

    def test_parse_types_and_dump_simple_bad(self):
        program = 'int'
        self.assertNotEqual([ast.dump(ast.parse('str').body[0].value, annotate_fields=False)]*2, AnnotationsUtils.parse_types_and_dump([program,program]))

    def test_parse_types_and_dump_complicated_bad(self):
        program = self.complicated_type_hint
        self.assertNotEqual([ast.dump(ast.parse('str').body[0].value, annotate_fields=False)]*2, AnnotationsUtils.parse_types_and_dump([program,program]))

    # compare_annotations_and_types

    def test_compare_annotations_and_types_simple(self):
        program = 'int'
        self.assertTrue(AnnotationsUtils.compare_annotations_and_types([ast.parse(program).body[0].value], [program]))

    def test_compare_annotations_and_types_complicated(self):
        program = self.complicated_type_hint
        self.assertTrue(AnnotationsUtils.compare_annotations_and_types([ast.parse(program).body[0].value], [program]))

    def test_compare_annotations_and_types_simple_bad(self):
        program = 'int'
        self.assertFalse(AnnotationsUtils.compare_annotations_and_types([ast.parse('str').body[0].value], [program]))

    def test_compare_annotations_and_types_complicated_bad(self):
        program = self.complicated_type_hint
        self.assertFalse(AnnotationsUtils.compare_annotations_and_types([ast.parse('str').body[0].value], [program]))

    # assertEqual_annotations_and_types
    def test_assertEqual_annotations_and_types_simple(self):
        program = 'int'
        try:
            AnnotationsUtils.assertEqual_annotations_and_types([ast.parse(program).body[0].value], [program])
        except AssertionError:
            self.fail("test_assertEqual_annotations_and_types_simple() raised AssertionError unexpectedly!")

    def test_assertEqual_annotations_and_types_complicated(self):
        program = self.complicated_type_hint
        try:
            AnnotationsUtils.assertEqual_annotations_and_types([ast.parse(program).body[0].value], [program])
        except AssertionError:
            self.fail("test_assertEqual_annotations_and_types_complicated() raised AssertionError unexpectedly!")

    def test_assertEqual_annotations_and_types_simple_bad(self):
        program = 'int'
        self.assertRaises(AssertionError, lambda:AnnotationsUtils.assertEqual_annotations_and_types([ast.parse('str').body[0].value], [program]))

    def test_assertEqual_annotations_and_types_complicated_bad(self):
        program = self.complicated_type_hint
        self.assertRaises(AssertionError, lambda:AnnotationsUtils.assertEqual_annotations_and_types([ast.parse('str').body[0].value], [program]))
