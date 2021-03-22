import ast

from typing import (
    Any,
    Dict,
    List,
)
from .visitor_base import (
    VisitorBase
)


class AssertVisitor(VisitorBase):

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None

        # Allow the raise visitor to be used in a mixin.
        super(AssertVisitor, self).__init__(*args, **kwargs)

        self.asserts = list()  # type: ast.AST

    @VisitorBase.continue_visiting
    def visit_Assert(self, node):
        # type: (ast.Assert) -> ast.AST:
        self.asserts.append(node)
