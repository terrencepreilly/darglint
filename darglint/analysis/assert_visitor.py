import ast

from typing import (
    Any,
    Dict,
    List,
)


class AssertVisitor(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None

        # Allow the raise visitor to be used in a mixin.
        # TODO: https://github.com/python/mypy/issues/4001
        super(AssertVisitor, self).__init__(*args, **kwargs)  # type: ignore

        self.asserts = list()  # type: List[ast.Assert]

    def visit_Assert(self, node):
        # type: (ast.Assert) -> ast.AST
        self.asserts.append(node)
        return self.generic_visit(node)
