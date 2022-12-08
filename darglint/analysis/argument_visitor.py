import ast
from typing import (
    Any,
    Dict,
    List,
)


class ArgumentVisitor(ast.NodeVisitor):
    """Reports which arguments a function contains."""

    def __init__(self, *args, **kwargs):
        # type: (List[Any], Dict[str, Any]) -> None

        # https://github.com/python/mypy/issues/5887
        super(ArgumentVisitor, self).__init__(*args, **kwargs)  # type: ignore

        # The arguments found in the function.
        self.arguments = list()  # type: List[str]
        self.types = list()  # type: List[str]

    def add_arg_by_name(self, name, arg):
        self.arguments.append(name)
        if arg.annotation is not None and hasattr(arg.annotation, 'id'):
            self.types.append(arg.annotation.id)
        else:
            self.types.append(None)

    def visit_arguments(self, node):
        # type: (ast.arguments) -> ast.AST
        if hasattr(node, 'posonlyargs'):
            annotatable_args = [*node.posonlyargs, *node.args]
        else:
            annotatable_args = node.args
        # make args with default values optional
        for index, default in enumerate(node.defaults):
            if default is not None:
                if hasattr(annotatable_args[-index - 1].annotation, 'id'):
                    if not 'optional' in annotatable_args[-index - 1].annotation.id.lower():
                        annotatable_args[
                            -index - 1
                        ].annotation.id = f'{annotatable_args[-index - 1].annotation.id}, optional'

        if hasattr(node, 'posonlyargs'):
            for arg in node.posonlyargs:
                self.add_arg_by_name(arg.arg, arg)

        for arg in node.args:
            self.add_arg_by_name(arg.arg, arg)

        for arg in node.kwonlyargs:
            self.add_arg_by_name(arg.arg, arg)

        # Handle single-star arguments.
        if node.vararg is not None:
            name = '*' + node.vararg.arg
            self.add_arg_by_name(name, node.vararg)

        if node.kwarg is not None:
            name = '**' + node.kwarg.arg
            self.add_arg_by_name(name, node.kwarg)
        return self.generic_visit(node)
