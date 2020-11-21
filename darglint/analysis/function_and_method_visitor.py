import ast
from typing import (
    Set,
)


class FunctionAndMethodVisitor(ast.NodeVisitor):

    def __init__(self):
        # type: () -> None
        self.callables = set()  # type: Set[ast.FunctionDef, ast.AsyncFunctionDef]
        self._methods = set()  # type: Set[ast.FunctionDef, ast.AsyncFunctionDef]

    @property
    def functions(self):
        # type: () -> Union[ast.FunctionDef, ast.AsyncFunctionDef]
        return list(self.callables - self._methods)

    @property
    def methods(self):
        # type: () -> Union[ast.FunctionDef, ast.AsyncFunctionDef]
        return list(self._methods)

    def visit_ClassDef(self, node):
        # type: (ast.ClassDef) -> ast.AST
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(
                item, ast.AsyncFunctionDef
            ):
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
