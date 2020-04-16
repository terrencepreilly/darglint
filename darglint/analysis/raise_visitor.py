import ast
from collections import (
    deque,
)
from typing import (
    Dict,
    Optional,
    Set,
)
from ..config import get_logger


logger = get_logger()


class Context(object):
    """A context which tracks exceptions and symbols."""

    def __init__(self):
        # type: () -> None
        self.exceptions = set()  # type: Set[str]

        # A lookup from variable names to AST nodes.
        # If the variable name occurs in a raise expression,
        # then the exception will be added using this lookup.
        self.variables = dict()  # type: Dict[str, str]

        # The error(s) which the current exception block is
        # handling. (Since we only handle one handler at a time
        # in the context, and since they don't repeat the
        # exception, it's fine to overwrite this value.)
        self.handling = None  # type: Optional[str]

    def _get_name_name(self, name):
        # type: (ast.Name) -> str
        return name.id

    def _get_exception_name(self, raises):
        # type: (ast.Raise) -> str
        if isinstance(raises, str):
            return raises
        if isinstance(raises.exc, ast.Name):
            # TODO: The name could come from a higher context --
            # we should check all parent contexts.
            name = raises.exc.id
            # The name was stored in the except statement,
            # so we should restore the type.
            if name in self.variables:
                return self.variables[name]
            else:
                return name
        elif isinstance(raises.exc, ast.Call):
            if hasattr(raises.exc.func, 'id'):
                return getattr(raises.exc.func, 'id')
            elif hasattr(raises.exc.func, 'attr'):
                return getattr(raises.exc.func, 'attr')
            else:
                logger.debug(
                    'Raises function call has neither id nor attr.'
                    'has only: %s' % str(dir(raises.exc.func))
                )
        elif isinstance(raises.exc, ast.Attribute):
            return raises.exc.attr
        elif isinstance(raises.exc, ast.Subscript):
            id_repr = ''
            if hasattr(raises.exc.value, 'id'):
                id_repr = getattr(raises.exc.value, 'id')
            n_repr = ''
            if hasattr(raises.exc.slice, 'value'):
                value = getattr(raises.exc.slice, 'value')
                if hasattr(value, 'n'):
                    n_repr = getattr(value, 'n')
            return '{}[{}]'.format(
                id_repr,
                n_repr,
            )
        elif raises.exc is None:
            return self.handling or ''
        else:
            logger.debug('Unexpected type in raises expression: {}'.format(
                raises.exc
            ))
        return ''

    def add_exception(self, node):
        # type: (ast.Raise) -> None
        self.exceptions.add(self._get_exception_name(node))

    def remove_exception(self, node):
        # type: (ast.Raise) -> None
        name = self._get_exception_name(node)
        if name in self.exceptions:
            self.exceptions.remove(name)
            self.handling = name

    def remove_all_exceptions(self):
        # type: () -> None
        self.exceptions = set()

    def add_variable(self, variable, exception):
        # type: (str, ast.Name) -> None
        self.variables[variable] = self._get_name_name(exception)

    def remove_variable(self, variable):
        # type: (str) -> None
        del self.variables[variable]

    def extend(self, other):
        # type: (Context) -> None
        self.exceptions |= other.exceptions

    def finish_handling(self):
        # type: () -> None
        self.handling = None


class RaiseVisitor(ast.NodeVisitor):

    def __init__(self):
        # The context in which an exception can be raised.
        # The default context is the function body,
        # and a new context is created for each try-except
        # statement.  When the current context is finished,
        # its errors are merged upwards.
        self.contexts = deque([Context()])

    @property
    def exceptions(self):
        # type: () -> Set[str]
        return self.contexts[0].exceptions

    @property
    def context(self):
        # type: () -> Context
        return self.contexts[-1]

    def visit_Raise(self, node):
        # type: (ast.Raise) -> ast.AST
        self.context.add_exception(node)
        return self.generic_visit(node)

    def visit_Try(self, node):
        # type: (ast.Try) -> None
        self.contexts.append(Context())
        for child in node.body:
            self.visit(child)
        for handler in node.handlers:
            if handler.type:
                if handler.name and isinstance(handler.type, ast.Name):
                    self.context.add_variable(handler.name, handler.type)
                id = getattr(handler.type, 'id', None)
                if id:
                    self.context.remove_exception(id)
            else:
                self.context.remove_all_exceptions()
        for handler in node.handlers:
            self.generic_visit(handler)

            # We need to signal that we've finished handling
            # the given handler section, otherwise the caught
            # error could bleed over into a bare except clause.
            self.context.finish_handling()
        context = self.contexts.pop()
        self.context.extend(context)
