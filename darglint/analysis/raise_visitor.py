import ast
from collections import (
    deque,
)
import copy
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Union,
)
from ..config import get_logger
from ..custom_assert import Assert


logger = get_logger()



class Context(object):
    """A context which tracks exceptions and symbols."""

    def __init__(self):
        # type: () -> None
        self.exceptions = set()  # type: Set[str]

        # If we're in a bare handler, we have to capture new
        # exceptions raised separately from the existing ones.
        # So, we copy the existing exceptions over here.
        # This complicates the logic, for the calling class (as
        # contextual operations have to account for two cases),
        # but it doesn't seem avoidable.
        self.bare_handler_exceptions = None # type: Optional[Set[str]]

        # A lookup from variable names to AST nodes.
        # If the variable name occurs in a raise expression,
        # then the exception will be added using this lookup.
        self.variables = dict()  # type: Dict[str, Union[str, List[str]]]

        # The error(s) which the current exception block is
        # handling. (Since we only handle one handler at a time
        # in the context, and since they don't repeat the
        # exception, it's fine to overwrite this value.)
        self.handling = None  # type: Optional[List[str]]

    def set_in_bare_handler(self):
        self.bare_handler_exceptions = set(self.exceptions)
        self.remove_all_exceptions()

    def _get_attr_name(self, attr):
        # type: (Union[ast.Attribute, ast.Name, ast.Tuple]) -> List[str]
        curr = attr  # type: Any
        parts = list()  # type: List[str]

        # We assume here that the ast has a limited
        # depth.  Even if it's several thousand long,
        # it should work fine.
        while curr:
            if isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            elif isinstance(curr, ast.Name):
                parts.append(curr.id)
                curr = None
            elif isinstance(curr, ast.Tuple):
                names = list()
                for node in curr.elts:
                    if isinstance(node, ast.Name):
                        names.extend(self._get_attr_name(node))
                    elif isinstance(node, ast.Attribute):
                        names.extend(self._get_attr_name(node))
                    else:
                        logger.error(
                            'While getting the names from a caught '
                            'tuple of exceptions, encountered '
                            'something other than an ast.Name: '
                            '{}'.format(
                                node.__class__.__name__
                            )
                        )
                return names
            else:
                logger.error(
                    'While getting ast.Attribute representation '
                    'a node had an unexpected type {}'.format(
                        curr.__class__.__name__
                    )
                )
                curr = None
        parts.reverse()
        return ['.'.join(parts)]

    def _get_name_name(self, name):
        # type: (Union[ast.Name, ast.Tuple]) -> Union[str, List[str]]
        if isinstance(name, ast.Name):
            return name.id
        elif isinstance(name, ast.Tuple):
            ret = list()
            for node in name.elts:
                if isinstance(node, ast.Name):
                    ret.append(node.id)
            return ret

    def _get_exception_name(self, raises):
        # type: (ast.Raise) -> Union[str, List[str]]
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
            if not self.handling:
                return ''
            elif len(self.handling) == 1:
                return self.handling[0]
            else:
                return self.handling
        else:
            logger.debug('Unexpected type in raises expression: {}'.format(
                raises.exc
            ))
        return ''

    def add_exception(self, node):
        # type: (ast.Raise) -> Set[str]
        """Add an exception to the context.

        If the exception(s) doesn't have a name and doesn't have
        more children, then it's a bare raise.  In that case, we
        return the exception(s) to the parent context.

        Args:
            node: A raise ast node.

        Returns:
            A list of exceptions to be passed up to the parent
            context.

        """
        name = self._get_exception_name(node)
        if name == '':
            if self.bare_handler_exceptions is not None:
                return self.bare_handler_exceptions | self.exceptions
            else:
                return self.exceptions
        if isinstance(name, str):
            self.exceptions.add(name)
        elif isinstance(name, list):
            for part in name:
                self.exceptions.add(part)
        else:
            logger.warning('Node {} name extraction failed.')
        return set()

    def remove_exception(self, node):
        # type: (ast.Raise) -> None
        name = self._get_exception_name(node)
        if isinstance(name, str) and name in self.exceptions:
            self.exceptions.remove(name)
            self.handling = [name]
        elif isinstance(name, list):
            self.handling = []
            for part in name:
                self.exceptions.remove(part)
                self.handling.append(part)

    def remove_all_exceptions(self):
        # type: () -> None
        self.exceptions = set()

    def add_variable(self, variable, exception):
        # type: (str, Union[ast.Name, ast.Tuple]) -> None
        self.variables[variable] = self._get_name_name(exception)

    def set_handling(self, attr):
        # type: (Union[ast.Attribute, ast.Name, ast.Tuple]) -> None
        self.handling = self._get_attr_name(attr)

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
        bubbles = self.context.add_exception(node)
        if bubbles:
            Assert(
                len(self.contexts) > 1,
                'We should only encounter bare raises in a handler.'
            )
            if len(self.contexts) < 2:
                return self.generic_visit(node)
            parent_context = self.contexts[-2]
            parent_context.exceptions |= bubbles

        return self.generic_visit(node)

    def visit_Try(self, node):
        # type: (ast.Try) -> None
        self.contexts.append(Context())
        for child in node.body:
            self.visit(child)
        for handler in node.handlers:
            if handler.type:
                if handler.name and (
                    isinstance(handler.type, ast.Name) or
                    isinstance(handler.type, ast.Tuple)
                ):
                    self.context.add_variable(handler.name, handler.type)
                elif isinstance(handler.type, ast.Attribute):
                    self.context.set_handling(handler.type)
                elif isinstance(handler.type, ast.Name):
                    self.context.set_handling(handler.type)
                elif isinstance(handler.type, ast.Tuple):
                    self.context.set_handling(handler.type)
                else:
                    logger.error(
                        'While getting the types of exceptions in '
                        'the handler, expected to find an ast.Name, '
                        'ast.Tuple, or ast.Attribute, but got {}'.format(
                            handler.type
                        )
                    )
                id = getattr(handler.type, 'id', None)
                if id:
                    self.context.remove_exception(id)

                self.generic_visit(handler)
                self.context.finish_handling()
            else:
                # Handle a bare except.
                #
                # Since the bare except handles all exceptions,
                # we have to clear all exceptions from the context.
                # However, exceptions could also be raised from
                # this handler.  So we can't clear the exceptions
                # first.  But if we clear the exceptions second,
                # then remove any new exceptions raised in the handler.
                # What we need, then, is to know which new exceptions
                # are raised, and clear all but them.  For that,
                # we use a temporary context.
                self.context.set_in_bare_handler()
                self.generic_visit(handler)

        for child in node.finalbody:
            self.visit(child)

        for child in node.orelse:
            self.visit(child)

        context = self.contexts.pop()
        self.context.extend(context)
