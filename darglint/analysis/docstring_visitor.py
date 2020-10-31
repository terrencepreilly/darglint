import ast
from typing import (
    List,
)


class DocstringVisitor(ast.NodeVisitor):

    def __init__(self):
        # type: () -> None
        self.docstrings = list()  # type: List[ast.Constant]

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        docstring = ast.get_docstring(node)
        if docstring:
            self.docstrings.append(docstring)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        docstring = ast.get_docstring(node)
        if docstring:
            self.docstrings.append(docstring)
        return self.generic_visit(node)
