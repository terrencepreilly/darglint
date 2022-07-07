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
        decorator_name = None
        if isinstance(decorator, ast.Name):
            # Attributes (setters and getters) won't have an id.
            decorator_name = decorator.id
        elif isinstance(decorator, ast.Attribute):
            decorator_name = decorator.attr

        if decorator_name in decorators:
            return True
    return False
