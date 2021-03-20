import ast
from unittest import (
    TestCase,
)
from darglint.analysis.pure_abstract_visitor import (
    PureAbstractVisitor,
)
from .utils import (
    reindent,
)


class PureAbstractVisitorTests(TestCase):
    def visitAbstract(self, program):
        function = ast.parse(reindent(program)).body[0]
        visitor = PureAbstractVisitor()
        visitor.visit(function)
        return visitor

    def assertPureAbstract(self, program):
        visitor = self.visitAbstract(program)
        self.assertTrue(visitor.is_pure_abstract)
        return visitor

    def assertNotPureAbstract(self, program):
        visitor = self.visitAbstract(program)
        self.assertFalse(visitor.is_pure_abstract)
        return visitor

    def check_abstract_decoration(self, program, result=True):
        visitor = self.visitAbstract(program)
        self.assertFalse(visitor.is_pure_abstract)
        visitor = self.visitAbstract("@abstractmethod\n" + reindent(program))
        self.assertEqual(visitor.is_pure_abstract, result)

    def check_abstract_toggle_doc(self, program, result=True, doc="None"):
        self.check_abstract_decoration(program.format(docstring=""), result)
        self.check_abstract_decoration(
            program.format(docstring=f'"""{doc}"""'),
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
