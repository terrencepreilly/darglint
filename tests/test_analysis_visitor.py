import ast
from unittest import TestCase

from .utils import reindent

from darglint.analysis.analysis_visitor import AnalysisVisitor


class AnalysisVisitorTests(TestCase):

    def assertFound(self, program, attribute, args, transform=None):
        """Assert that the given attribute values were found.

        Args:
            program: The program to run the analysis on.
            attribute: The attribute which should be checked.
            args: The value(s) which should exist in the attribute.
            transform: If supplied, a function which transforms
                the attribute values prior to comparison.

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
            actual,
            args,
        )
        return visitor

    def test_analyze_single_function_with_everything(self):
        program = r'''
            def f(x):
                """Halves the argument."""
                assert x > 0
                ret = x / 2
                if ret < 0:
                    raise Exception('It\'s less than 0!')
                yield None
                return ret
        '''
        self.assertFound(program, 'arguments', ['x'])
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
