import ast
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)


class ReturnVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(ReturnVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.returns = list()  # type: List[Optional[ast.Return]]
        self.return_types = list()  # type: List[Optional[ast.AST]]

    def _visit_function(self, node):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> ast.AST
        if node.returns is None:
            self.return_types.append(None)
        else:
            self.return_types.append(node.returns)
        return super(ReturnVisitor, self).generic_visit(node)

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        return self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        return self._visit_function(node)

    def visit_Return(self, node):
        # type: (ast.Return) -> ast.AST
        self.returns.append(node)
        return self.generic_visit(node)
