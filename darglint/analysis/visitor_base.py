import ast
from functools import wraps


class VisitorBase(ast.NodeVisitor):
    def continue_visiting(function):
        @wraps(function)
        def continuation(self, node):
            function(self, node)
            return getattr(super(), function.__name__, super().generic_visit)(node)

        return continuation
