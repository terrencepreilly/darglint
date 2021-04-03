import ast
from typing import (
    Any,
    Dict,
    List,
)

from .analysis_helpers import (
    _has_decorator
)

class AbstractCallableVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_abstract = None

    def _is_docstring(self, node):
        # type: (ast.AST) -> bool
        return (
            isinstance(node, ast.Expr) and (
                (
                    isinstance(node.value, ast.Constant) and
                    isinstance(node.value.value, str)
                ) or (
                    isinstance(node.value, ast.Str) # Python < 3.8
                )
            )
        )

    def _is_ellipsis(self, node):
        # type: (ast.AST) -> bool

        return (
            isinstance(node, ast.Expr) and (
                (
                    isinstance(node.value, ast.Constant) and
                    node.value.value is Ellipsis
                ) or (
                    isinstance(node.value, ast.Ellipsis) # Python < 3.8
                )
            )
        )

    def _is_raise_NotImplementedException(self, node):
        # type: (ast.AST) -> bool
        return (
            isinstance(node, ast.Raise) and (
                (
                    isinstance(node.exc, ast.Name) and
                    node.exc.id == "NotImplementedError"
                ) or (
                    isinstance(node.exc, ast.Call)
                    and isinstance(node.exc.func, ast.Name)
                    and node.exc.func.id == "NotImplementedError"
                )
            )
        )

    def _is_return_NotImplemented(self, node):
        # type: (ast.AST) -> bool
        return (
            isinstance(node, ast.Return) and
            isinstance(node.value, ast.Name) and
            node.value.id == "NotImplemented"
        )

    def analyze_pure_abstract(self, node):
        # type: (ast.AST) -> bool
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)), (
            "Assuming this analysis is only called on functions"
        )

        if not _has_decorator(node, "abstractmethod"):
            return False

        children = len(node.body)

        # maximum docstring and one statement
        if children > 2:
            return False

        if children == 2:
            if not self._is_docstring(node.body[0]):
                return False

            statement = node.body[1]
        else:
            statement = node.body[0]

        if (
            isinstance(statement, ast.Pass) or
            self._is_ellipsis(statement) or
            self._is_raise_NotImplementedException(statement) or
            self._is_return_NotImplemented(statement) or
            (
                children == 1 and
                self._is_docstring(statement)
            )
        ):
            return True

        return False

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        self.is_abstract = self.analyze_pure_abstract(node)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        self.is_abstract = self.analyze_pure_abstract(node)
        return self.generic_visit(node)
