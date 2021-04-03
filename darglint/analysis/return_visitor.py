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
        # type: (Any, Any) -> None

        # TODO: https://github.com/python/mypy/issues/4001
        super(ReturnVisitor, self).__init__(*args, **kwargs)  # type: ignore

        # A list of the return nodes encountered.
        self.returns = list()  # type: List[Optional[ast.Return]]
        self.return_types = list()  # type: List[Optional[ast.AST]]

    def visit_Return(self, node):
        # type: (ast.Return) -> ast.AST
        self.returns.append(node)
        return self.generic_visit(node)
