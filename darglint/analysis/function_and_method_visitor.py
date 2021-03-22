import ast
from typing import (
    Set,
)

from .visitor_base import (
    VisitorBase
)


class FunctionAndMethodVisitor(VisitorBase):

    def __init__(self):
        # type: () -> None
        self.callables = set()  # type: Set[ast.FunctionDef, ast.AsyncFunctionDef]
        self._methods = set()  # type: Set[ast.FunctionDef, ast.AsyncFunctionDef]
        self._properties = set()  # type: Set[ast.FunctionDef, ast.AsyncFunctionDef]

    @property
    def functions(self):
        # type: () -> Union[ast.FunctionDef, ast.AsyncFunctionDef]
        return list(self.callables - self._methods - self._properties)

    @property
    def methods(self):
        # type: () -> Union[ast.FunctionDef, ast.AsyncFunctionDef]
        return list(self._methods)

    @property
    def properties(self):
        # type: () -> Union[ast.FunctionDef, ast.AsyncFunctionDef]
        return list(self._properties)

    @VisitorBase.continue_visiting
    def visit_ClassDef(self, node):
        # type: (ast.ClassDef) -> ast.AST
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(
                item, ast.AsyncFunctionDef
            ):
                if self._has_decorator(item, "property"):
                    self._properties.add(item)
                else:
                    self._methods.add(item)

    @VisitorBase.continue_visiting
    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        self.callables.add(node)

    @VisitorBase.continue_visiting
    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        self.callables.add(node)
