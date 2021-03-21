import ast
from typing import (
    Any,
    Dict,
    List,
)


def _is_docstring(node):
    # type: (ast.Return) -> bool
    return (
        isinstance(node, ast.Expr) and (
            (
                isinstance(node.value, ast.Constant) and
                isinstance(node.value.value, str)
            ) or (
                isinstance(node.value, ast.Str) # Python < 3.8
            )
        )
    )

def _is_ellipsis(node):
    # type: (ast.Return) -> bool
    print(f"{getattr(node,'value','')} ellipsis")

    return (
        isinstance(node, ast.Expr) and (
            (
                isinstance(node.value, ast.Constant) and
                node.value.value is Ellipsis
            ) or (
                isinstance(node.value, ast.Ellipsis) # Python < 3.8
            )
        )
    )

def _is_raise_NotImplementedException(node):
    # type: (ast.Return) -> bool
    return (
        isinstance(node, ast.Raise) and (
            (
                isinstance(node.exc, ast.Name) and
                node.exc.id == "NotImplementedError"
            ) or (
                isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id == "NotImplementedError"
            )
        )
    )

def _is_return_NotImplemented(node):
    # type: (ast.Return) -> bool
    return (
        isinstance(node, ast.Return) and
        isinstance(node.value, ast.Name) and
        node.value.id == "NotImplemented"
    )

def _is_abstract(node):
    # type: (ast.Return) -> bool
    for decorator in node.decorator_list:
        # apparently there can be decorators without id's
        if getattr(decorator, "id", "") == ("abstractmethod"):
            return True

    return False

def analyze_pure_abstract(node):
    # type: (ast.Return) -> bool
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)), (
        "Assuming this analysis is only called on functions"
    )

    if not _is_abstract(node):
        return False

    children = len(node.body)

    # maximum docstring and one statement
    if children > 2:
        return False

    if children == 2:
        if not _is_docstring(node.body[0]):
            return False

        statement = node.body[1]
    else:
        statement = node.body[0]

    if (
        isinstance(statement, ast.Pass) or
        _is_ellipsis(statement) or
        _is_raise_NotImplementedException(statement) or
        _is_return_NotImplemented(statement) or
        (
            children == 1 and
            _is_docstring(statement)
        )
    ):
        return True

    return False
