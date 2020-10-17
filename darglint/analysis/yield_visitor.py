import ast
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)


class YieldVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        super(YieldVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.yields = list()  # type: List[ast.Yield]

    def visit_Yield(self, node):
        # type: (ast.Yield) -> ast.AST
        self.yields.append(node)
        return self.generic_visit(node)

