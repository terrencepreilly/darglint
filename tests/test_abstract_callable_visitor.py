import ast
from unittest import (
    TestCase,
)
from darglint.analysis.abstract_callable_visitor import (
    AbstractCallableVisitor,
)
from darglint.analysis.analysis_visitor import (
    AnalysisVisitor
)
from .utils import (
    reindent,
)


class PureAbstractVisitorTests(TestCase):
    def analyzeAbstract(self, program):
        function = ast.parse(reindent(program)).body[0]
        #visitor = AnalysisVisitor()
        visitor = AbstractCallableVisitor()
        visitor.visit(function)
        return visitor

    def check_abstract_decoration(self, program, result=True):
        visitor = self.analyzeAbstract(program)
        self.assertFalse(visitor.is_abstract)
        visitor = self.analyzeAbstract("@abstractmethod\n" + reindent(program))
        self.assertEqual(visitor.is_abstract, result)
        visitor = self.analyzeAbstract("@abc.abstractmethod\n" + reindent(program))
        self.assertEqual(visitor.is_abstract, result)

    def check_abstract_toggle_doc(self, program, result=True, doc="None"):
        self.check_abstract_decoration(program.format(docstring=""), result)
        self.check_abstract_decoration(
            program.format(docstring='"""{}"""'.format(doc)),
            result
        )

    def test_pass(self):
        program = r"""
            def f():
                {docstring}
                pass
        """
        self.check_abstract_toggle_doc(program)

    def test_return(self):
        program = r"""
            def f():
                {docstring}
                return 2
        """
        self.check_abstract_toggle_doc(program, False)

    def test_ellipsis(self):
        program = r"""
            def f():
                {docstring}
                ...
        """
        self.check_abstract_toggle_doc(program)

    def test_constant(self):
        program = r"""
            def f():
                {docstring}
                42
        """
        self.check_abstract_toggle_doc(program, False)

    def test_not_implemented_exception(self):
        program = r"""
            def f():
                {docstring}
                raise NotImplementedError
        """
        self.check_abstract_toggle_doc(program)

    def test_not_implemented_exception_reason(self):
        program = r"""
            def f():
                {docstring}
                raise NotImplementedError("Malte did not want to.")
        """
        self.check_abstract_toggle_doc(program)

    def test_not_implemented(self):
        program = r"""
            def f():
                {docstring}
                return NotImplemented
        """
        self.check_abstract_toggle_doc(program)

    def test_only_docstring(self):
        program = r'''
            def f():
                """Documented empty body."""
        '''
        self.check_abstract_decoration(program)
