import ast
from functools import wraps
from typing import (
    Iterable,
    Union
)


class VisitorBase(ast.NodeVisitor):
    def continue_visiting(function):
        @wraps(function)
        def continuation(self, node):
            function(self, node)
            return getattr(super(), function.__name__, super().generic_visit)(node)

        return continuation
    
    def _has_decorator(self, function, decorators):
        # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Union[str, Iterable[str]]) -> bool
        if isinstance(decorators, str):
            decorators = (decorators,)

        for decorator in function.decorator_list:
            # Attributes (setters and getters) won't have an id.
            if isinstance(decorator, ast.Name) and decorator.id in decorators:
                return True
        return False
