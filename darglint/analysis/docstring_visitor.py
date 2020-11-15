import ast
from typing import (
    Any,
    Dict,
    List,
)


class DocstringVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None

        # Allow the raise visitor to be used in a mixin.
        super(DocstringVisitor, self).__init__(*args, **kwargs)

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
