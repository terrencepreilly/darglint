import ast
from typing import (
    Iterable,
    Union
)

def _has_decorator(function, decorators):
    # # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Union[str, Iterable[str]]) -> bool
    if isinstance(decorators, str):
        decorators = (decorators,)

    for decorator in function.decorator_list:
        # Attributes (setters and getters) won't have an id.
        if isinstance(decorator, ast.Name) and decorator.id in decorators:
            return True
    return False
