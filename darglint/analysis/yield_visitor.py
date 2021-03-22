import ast
from typing import (
    Any,
    Dict,
    List,
)
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)
from .visitor_base import (
    VisitorBase
)


class YieldVisitor(VisitorBase):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(YieldVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.yields = list()  # type: List[Union[ast.Yield, ast.YieldFrom]]

    @VisitorBase.continue_visiting
    def visit_Yield(self, node):
        # type: (ast.Yield) -> ast.AST
        self.yields.append(node)

    @VisitorBase.continue_visiting
    def visit_YieldFrom(self, node):
        # type: (ast.Yield) -> ast.AST
        self.yields.append(node)
