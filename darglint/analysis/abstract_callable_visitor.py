import ast
from typing import (
    Any,
    Dict,
    List,
)
from .pure_abstract_analyzer import (
    analyze_pure_abstract,
)


class AbstractCallableVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(AbstractCallableVisitor, self).__init__(*args, **kwargs)

        self.is_abstract = None

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        self.is_abstract = analyze_pure_abstract(node)
        return super().visit_FunctionDef(node)

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        self.is_abstract = analyze_pure_abstract(node)
        return super().visit_AsyncFunctionDef(node)
