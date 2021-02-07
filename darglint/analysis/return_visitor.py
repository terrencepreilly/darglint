import ast
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)


class ReturnVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(ReturnVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.returns = list()  # type: List[Optional[ast.Return]]
        self.return_types = list()  # type: List[Optional[ast.AST]]

    def visit_Return(self, node):
        # type: (ast.Return) -> ast.AST
        self.returns.append(node)
        return self.generic_visit(node)
