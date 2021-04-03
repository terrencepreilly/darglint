import ast
from typing import (
    List,
    Set,
    Union,
)

from .analysis_helpers import (
    _has_decorator
)


class FunctionAndMethodVisitor(ast.NodeVisitor):

    def __init__(self):
        # type: () -> None
        self.callables = set()  # type: Set[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
        self._methods = set()  # type: Set[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
        self._properties = set()  # type: Set[Union[ast.FunctionDef, ast.AsyncFunctionDef]]

    @property
    def functions(self):
        # type: () -> List[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
        return list(self.callables - self._methods - self._properties)

    @property
    def methods(self):
        # type: () -> List[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
        return list(self._methods)

    @property
    def properties(self):
        # type: () -> List[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
        return list(self._properties)

    def visit_ClassDef(self, node):
        # type: (ast.ClassDef) -> ast.AST
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(
                item, ast.AsyncFunctionDef
            ):
                if _has_decorator(item, "property"):
                    self._properties.add(item)
                else:
                    self._methods.add(item)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        self.callables.add(node)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        self.callables.add(node)
        return self.generic_visit(node)
