import ast
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)


class YieldVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None

        # TODO: https://github.com/python/mypy/issues/4001
        super(YieldVisitor, self).__init__(*args, **kwargs)  # type: ignore

        # A list of the return nodes encountered.
        self.yields = list()  # type: List[Union[ast.Yield, ast.YieldFrom]]

    def visit_Yield(self, node):
        # type: (ast.Yield) -> ast.AST
        self.yields.append(node)
        return self.generic_visit(node)

    def visit_YieldFrom(self, node):
        # type: (ast.YieldFrom) -> ast.AST
        self.yields.append(node)
        return self.generic_visit(node)
