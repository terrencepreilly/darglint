import ast

from typing import (
    Any,
)

class FunctionScopedVisitorMixin(ast.NodeVisitor):
    """A visitor which is scoped to a single function.

    This visitor assumes that its `visit` method is called
    on a `ast.FunctionDef`, and it will not examine nested
    functions.

    """

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None

        # TODO: https://github.com/python/mypy/issues/4001
        super(FunctionScopedVisitorMixin, self).__init__(*args, **kwargs)  # type: ignore  # noqa: E501

        # Whether we have passed the initial `FunctionDef` node.
        self.in_function = False

    def visit_Lambda(self, node):
        # type: (ast.Lambda) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return getattr(
                super(),
                "visit_Lambda",
                super().generic_visit
            )(node)
        else:
            # Return a synthetic Pass node, to make type checking happy
            # (and to not violate the contract.)  Since it has no children,
            # it will effectively stop the visit.
            return ast.Pass()

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return getattr(
                super(),
                "visit_FunctionDef",
                super().generic_visit
            )(node)
        else:
            return ast.Pass()

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return getattr(
                super(),
                "visit_AsyncFunctionDef",
                super().generic_visit
            )(node)
        else:
            return ast.Pass()
