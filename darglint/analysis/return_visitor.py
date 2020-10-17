import ast
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)


class ReturnVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        super(ReturnVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.returns = list()  # type: List[ast.Return]

    def visit_Return(self, node):
        # type: (ast.Return) -> ast.AST
        self.returns.append(node)
        return self.generic_visit(node)
