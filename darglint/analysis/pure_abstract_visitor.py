import ast
from typing import (
    Any,
    Dict,
    List,
)


class PureAbstractVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(PureAbstractVisitor, self).__init__(*args, **kwargs)

        self.is_pure_abstract = False

    def _is_docstring(self, node):
        # type: (ast.Return) -> bool
        return (
            isinstance(node, ast.Expr) and
            isinstance(node.value, ast.Constant) and
            isinstance(node.value.value, str)
        )

    def _is_ellipsis(self, node):
        # type: (ast.Return) -> bool
        return (
            isinstance(node, ast.Expr) and
            isinstance(node.value, ast.Constant) and
            node.value.value is Ellipsis
        )

    def _is_raise_NotImplementedException(self, node):
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

    def _is_return_NotImplemented(self, node):
        # type: (ast.Return) -> bool
        return (
            isinstance(node, ast.Return) and
            isinstance(node.value, ast.Name) and
            node.value.id == "NotImplemented"
        )

    def _is_abstract(self, node):
        # type: (ast.Return) -> bool
        for decorator in node.decorator_list:
            if decorator.id in ("abstractmethod",):
                return True

        return False

    def visit(self, node):
        # type: (ast.Return) -> ast.AST
        assert isinstance(node, ast.FunctionDef), (
            "Assuming this Visitor is only called on functions"
        )

        self.is_pure_abstract = False

        if not self._is_abstract(node):
            return node

        children = len(node.body)

        # maximum docstring and one statement
        if children > 2:
            return node

        if children == 2:
            if not self._is_docstring(node.body[0]):
                return node

            statement = node.body[1]
        else:
            statement = node.body[0]

        if (
            isinstance(statement, ast.Pass) or
            self._is_ellipsis(statement) or
            self._is_raise_NotImplementedException(statement) or
            self._is_return_NotImplemented(statement) or
            (
                children == 1 and
                self._is_docstring(statement)
            )
        ):
            self.is_pure_abstract = True

        return node
