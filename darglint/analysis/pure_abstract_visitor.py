import ast
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)
from ..config import (
    get_logger,
)
from ..custom_assert import (
    Assert,
)

from pprint import pprint


class PureAbstractVisitor(ast.NodeVisitor):
    """A visitor which checks for *returns* nodes."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None
        super(PureAbstractVisitor, self).__init__(*args, **kwargs)

        # A list of the return nodes encountered.
        self.is_abstract = False
        self.has_implementation = False
        self._toplevel_function = True
        self.returns = list()  # type: List[Optional[ast.Return]]
        self.return_types = list()  # type: List[Optional[ast.AST]]

    @property
    def is_pure_abstract(self):
        return self.is_abstract and not self.has_implementation

    def generic_visit(self, node):
        # type: (ast.Return) -> ast.AST
        node_visit_function = f"visit_{node.__class__.__name__}"

        if not hasattr(self, node_visit_function):
            print(f"Making non pure since there is no {node_visit_function}")
            self.has_implementation = True
            return node

        return super().generic_visit(node)

    def visit_FunctionDef(self, node):
        # type: (ast.Return) -> ast.AST
        if self._toplevel_function:
            self._toplevel_function = False

            for decorator in node.decorator_list:
                if decorator.id in ("abstractmethod",):
                    self.is_abstract = True
                else:
                    print(f"not found {decorator.id}")
                    return node

            # only inspect the body
            for body_node in node.body:
                self.visit(body_node)

            self._toplevel_function = True
            return node
        else:
            return self.generic_visit(node)

    def visit_arguments(self, node):
        # type: (ast.Return) -> ast.AST
        return node

    def visit_Pass(self, node):
        # type: (ast.Return) -> ast.AST
        # return self.generic_visit(node)
        print("Entered pass visit")
        return node

    # Python 3.8+
    def visit_Constant(self, node):
        # type: (ast.Return) -> ast.AST
        if node.value is Ellipsis:
            return self.generic_visit(node)

        # docstrings
        if isinstance(node.value, str):
            return self.generic_visit(node)

        self.has_implementation = True

        return self.generic_visit(node)

    # Deprecated after Python 3.8
    def visit_Ellipsis(self, node):
        # type: (ast.Return) -> ast.AST
        return node

    def visit_Expr(self, node):
        # an Ellipsis is wrapped in this, so we ignore expression nodes
        # since an expression node always has children those decide if
        # the function is actually abstract or not.
        return self.generic_visit(node)

    def visit_Raise(self, node):
        # type: (ast.Return) -> ast.AST

        # raise NotImplementedException
        if isinstance(node.exc, ast.Name) and node.exc.id in (
            "NotImplementedException",
        ):
            return node

        # raise NotImplementedException("reason")
        if (
            isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and node.exc.func.id in ("NotImplementedException",)
        ):
            return node

        self.has_implementation = True
        return node

    def visit_Return(self, node):
        if not (
            isinstance(node.value, ast.Name) and node.value.id in ("NotImplemented",)
        ):
            self.has_implementation = True

        return node
