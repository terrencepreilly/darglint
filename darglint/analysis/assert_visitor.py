import ast


class AssertVisitor(ast.NodeVisitor):

    def __init__(self):
        self.asserts = list()  # type: ast.AST

    def visit_Assert(self, node):
        # type: (ast.Assert) -> ast.AST:
        self.asserts.append(node)
        return self.generic_visit(node)
