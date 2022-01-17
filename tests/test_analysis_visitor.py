import ast

from darglint.analysis.analysis_visitor import AnalysisVisitor
from darglint.utils import AnnotationsUtils, AstNodeUtils

from .utils import TestCase, reindent


class AnalysisVisitorTests(TestCase):

    def assertFound(self, program, attribute, args, transform=None, postprocess_actual=None):
        """Assert that the given attribute values were found.

        Args:
            program: The program to run the analysis on.
            attribute: The attribute which should be checked.
            args: The value(s) which should exist in the attribute.
            transform: If supplied, a function which transforms
                the attribute values prior to comparison.
            postprocess_actual: postprocess actual value

        Returns:
            The visitor, in case you want to do more analysis.

        """
        function = ast.parse(reindent(program))
        visitor = AnalysisVisitor()
        visitor.visit(function)
        actual = getattr(visitor, attribute)
        if transform:
            if isinstance(actual, list):
                actual = list(map(transform, actual))
            elif isinstance(actual, set):
                actual = set(map(transform, actual))
            else:
                actual = transform(actual)
        self.assertEqual(
            actual if postprocess_actual is None else postprocess_actual(actual),
            args,
        )
        return visitor

    def test_analyze_single_function_with_everything(self):
        program = r'''
            def f(x: int) -> int:
                """Halves the argument."""
                assert x > 0
                ret = x / 2
                if ret < 0:
                    raise Exception('It\'s less than 0!')
                yield None
                return ret
        '''
        self.assertFound(program, 'arguments', ['x'])
        self.assertFound(program, 'annotations', AnnotationsUtils.parse_types_and_dump(['int']), postprocess_actual=AstNodeUtils.dump)
        self.assertFound(program, 'exceptions', {'Exception'})

        # Just check that an assert is present by registering a number.
        self.assertFound(program, 'asserts', [1], lambda x: 1)
        self.assertFound(program, 'returns', [1], lambda x: 1)

        self.assertFound(program, 'variables', ['ret'], lambda x: x.id)
        self.assertFound(program, 'yields', [1], lambda x: 1)

    def test_analyze_single_function_with_everything_with_complicated_types(self):
        program = r'''
            def f(x: {}) -> int:
                """Halves the argument."""
                assert x > 0
                ret = x / 2
                if ret < 0:
                    raise Exception('It\'s less than 0!')
                yield None
                return ret
        '''.format(self.complicated_type_hint)
        self.assertFound(program, 'arguments', ['x'])
        self.assertFound(program, 'annotations', AnnotationsUtils.parse_types_and_dump([self.complicated_type_hint]), postprocess_actual=AstNodeUtils.dump)
        self.assertFound(program, 'exceptions', {'Exception'})

        # Just check that an assert is present by registering a number.
        self.assertFound(program, 'asserts', [1], lambda x: 1)
        self.assertFound(program, 'returns', [1], lambda x: 1)

        self.assertFound(program, 'variables', ['ret'], lambda x: x.id)
        self.assertFound(program, 'yields', [1], lambda x: 1)

    def test_only_current_function_checked(self):
        program = r'''
            def f(x):
                """Halves the argument."""
                def _inner():
                    r = x / 2
                    if r < 0:
                        raise Exception('It\'s less than 0!')
                    return r
                return _inner()
        '''
        self.assertFound(program, 'returns', [1], lambda x: 1)

    def test_finds_abstract(self):
        program = r'''
            @abstractmethod
            def f(x):
                """Halves the argument."""
                pass
        '''
        function = ast.parse(reindent(program))
        visitor = AnalysisVisitor()
        visitor.visit(function)
        self.assertTrue(visitor.is_abstract, 'Should have been marked abstract.')

    def test_finds_not_abstract(self):
        program = r'''
            def f(x):
                """Halves the argument."""
                return x / 2
        '''
        function = ast.parse(reindent(program))
        visitor = AnalysisVisitor()
        visitor.visit(function)
        self.assertFalse(visitor.is_abstract, 'Should have been marked abstract.')
