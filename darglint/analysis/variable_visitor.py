import ast
from typing import (
    Any,
    Dict,
    List,
)
from .visitor_base import (
    VisitorBase
)

class VariableVisitor(VisitorBase):

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(VariableVisitor, self).__init__(*args, **kwargs)
        self.variables = list()  # type: List[ast.Name]

    @VisitorBase.continue_visiting
    def visit_Name(self, node):
        # type: (ast.Name) -> ast.AST
        # Only gather names during assignment.  Others are unnecessary,
        # and could be from a different context.
        if hasattr(node, 'ctx') and isinstance(node.ctx, ast.Store):
            self.variables.append(node)
