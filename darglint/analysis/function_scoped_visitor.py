import ast

class FunctionScopedVisitorMixin(ast.NodeVisitor):
    """A visitor which is scoped to a single function.

    This visitor assumes that its `visit` method is called
    on a `ast.FunctionDef`, and it will not examine nested
    functions.

    """

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(FunctionScopedVisitorMixin, self).__init__(*args, **kwargs)

        # Whether we have passed the initial `FunctionDef` node.
        self.in_function = False

    def visit_Lambda(self, node):
        # type: (ast.Lambda) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # type: (ast.FunctionDef) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        # type: (ast.AsyncFunctionDef) -> ast.AST
        if not self.in_function:
            self.in_function = True
            return self.generic_visit(node)
