"""A linter for docstrings following the google docstring format."""
import ast
from collections import deque
import sys
from typing import (
    Callable,
    Iterator,
    List,
    Set,
    Tuple,
    Optional,
    Union,
    Type,
    Any,
)

from .analysis.raise_visitor import (
    RaiseVisitor,
)
from .config import get_logger


logger = get_logger()


FunctionDef = ast.FunctionDef  # type: Union[Type[Any], Tuple[Type[Any], Type[Any]]]  # noqa: E501
if hasattr(ast, 'AsyncFunctionDef'):
    FunctionDef = (ast.FunctionDef, ast.AsyncFunctionDef)


def read_program(filename):  # type: (str) -> Union[bytes, str]
    """Read a program from a file.

    Args:
        filename: The name of the file to read. If set to '-', then we will
            read from stdin.

    Returns:
        The program as a single string.

    """
    program = None  # type: Union[bytes, Optional[str]]
    if filename == '-':
        program = sys.stdin.read()
    else:
        with open(filename, 'rb') as fin:
            program = fin.read()
    return program or ''


def _get_arguments(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Tuple[List[str], List[str]]  # noqa: E501
    arguments = list()  # type: List[str]
    types = list()  # type: List[str]

    def add_arg_by_name(name, arg):
        arguments.append(name)
        if arg.annotation is not None and hasattr(arg.annotation, 'id'):
            types.append(arg.annotation.id)
        else:
            types.append(None)

    if hasattr(fn.args, 'posonlyargs'):
        for arg in fn.args.posonlyargs:
            add_arg_by_name(arg.arg, arg)

    for arg in fn.args.args:
        add_arg_by_name(arg.arg, arg)

    for arg in fn.args.kwonlyargs:
        add_arg_by_name(arg.arg, arg)

    # Handle single-star arguments.
    if fn.args.vararg is not None:
        name = '*' + fn.args.vararg.arg
        add_arg_by_name(name, fn.args.vararg)

    if fn.args.kwarg is not None:
        name = '**' + fn.args.kwarg.arg
        add_arg_by_name(name, fn.args.kwarg)

    return arguments, types


def _walk(fun, skip):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef], Callable) -> Iterator[ast.AST]  # noqa: E501
    """Walk through the nodes in this function, skipping as necessary.

    ast.walk goes through nodes in an arbitrary order, and doesn't
    allow you to skip an entire branch (as far as I know.)  This
    function will perform an in-order breadth-first traversal, and will
    skip unnecessary branches.

    Args:
        fun: The function to walk.
        skip: A function which returns True if we should skip the current
            node and all of its children.

    Yields:
        Children of the function and the function itself.

    """
    queue = deque()  # type: deque
    queue.appendleft(fun)
    while len(queue) > 0:
        curr = queue.pop()
        if skip(curr):
            continue
        if hasattr(curr, 'body'):
            queue.extendleft(curr.body)
        if hasattr(curr, 'handlers'):
            queue.extendleft(curr.handlers)
        if hasattr(curr, 'orelse'):
            queue.extendleft(curr.orelse)
        yield curr


def _has_return(fun):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool
    """Return true if the function has a fruitful return.

    Args:
        fun: A function node to check.

    Returns:
        True if there is a fruitful return, otherwise False.

    """
    def skip(f):
        return f != fun and isinstance(f, FunctionDef)

    for node in _walk(fun, skip):
        if isinstance(node, ast.Return) and node.value is not None:
            return True
    return False


def _has_yield(fun):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool  # noqa: E501
    for node in ast.walk(fun):
        if isinstance(node, ast.Yield) or isinstance(node, ast.YieldFrom):
            return True
    return False


def _get_docstring(fun):  # type: (ast.AST) -> str
    return ast.get_docstring(fun)


def _get_all_functions(tree):  # type: (ast.AST) -> Iterator[Union[ast.FunctionDef, ast.AsyncFunctionDef]]  # noqa: E501
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            yield node
        elif hasattr(ast, 'AsyncFunctionDef'):
            if isinstance(node, ast.AsyncFunctionDef):
                yield node


def _get_all_classes(tree):  # type: (ast.AST) -> Iterator[ast.ClassDef]
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _get_all_methods(tree):  # type: (ast.AST) -> Iterator[Union[ast.FunctionDef, ast.AsyncFunctionDef]]  # noqa: E501
    for klass in _get_all_classes(tree):
        for fun in _get_all_functions(klass):
            yield fun


def _get_decorator_names(fun):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]  # noqa: E501
    """Get decorator names from the function.

    Args:
        fun: The function whose decorators we are getting.

    Returns:
        The names of the decorators. Does not include setters and
        getters.

    """
    ret = list()
    for decorator in fun.decorator_list:
        # Attributes (setters and getters) won't have an id.
        if hasattr(decorator, 'id'):
            ret.append(getattr(decorator, 'id'))
    return ret


def _is_classmethod(fun):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool  # noqa: E501
    return 'classmethod' in _get_decorator_names(fun)


def _is_staticmethod(fun):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool  # noqa: E501
    return 'staticmethod' in _get_decorator_names(fun)


def _get_stripped_method_args(method):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Tuple[List[str], List[str]]  # noqa: E501
    args, types = _get_arguments(method)
    if 'cls' in args and _is_classmethod(method):
        args.remove('cls')
        types.pop(0)
    elif 'self' in args and not _is_staticmethod(method):
        args.remove('self')
        types.pop(0)
    return args, types


def _get_all_raises(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Iterator[ast.Raise]  # noqa: E501
    for node in ast.walk(fn):
        if isinstance(node, ast.Raise):
            yield node


def _get_exception_name(raises):  # type: (ast.Raise) -> str
    if isinstance(raises.exc, ast.Name):
        return raises.exc.id
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
    else:
        logger.debug('Unexpected type in raises expression: {}'.format(
            raises.exc
        ))
    return ''


def _get_exceptions_raised(fn):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Set[str]  # noqa: E501
    visitor = RaiseVisitor()
    visitor.visit(fn)
    return visitor.exceptions


def _raises_assert(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool  # noqa: E501
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
    return False

def _get_return_type(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]
    if fn.returns is not None and hasattr(fn.returns, 'id'):
        return getattr(fn.returns, 'id')
    return None


def _get_all_variable_names(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Iterator[str]
    """Get all variable names used in the function.

    Args:
        fn: The function.

    Yields:
        The nodes which represent names.

    """
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            yield node.id


def get_line_number_from_function(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> int
    """Get the line number for the end of the function signature.

    The function signature can be farther down when the parameter
    list is split across multiple lines.

    Args:
        fn: The function from which we are getting the line number.

    Returns:
        The line number for the start of the docstring for this
        function.

    """
    line_number = fn.lineno
    if hasattr(fn, 'args') and fn.args.args:
        last_arg = fn.args.args[-1]
        line_number = last_arg.lineno
    return line_number


class FunctionDescription(object):
    """Describes a function or method.

    Whereas a `Docstring` object describes a function's docstring,
    a `FunctionDescription` describes the function itself.  (What,
    ideally, the docstring should describe.)

    """

    def __init__(self, is_method, function):
        # type: (bool, Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None
        """Create a new FunctionDescription.

        Args:
            is_method: True if this is a method. Will attempt to remove
                self or cls if appropriate.
            function: The base node of the function.

        """
        self.is_method = is_method
        self.function = function
        self.line_number = get_line_number_from_function(function)
        self.name = function.name
        if is_method:
            self.argument_names, self.argument_types = (
                _get_stripped_method_args(function)
            )
        else:
            self.argument_names, self.argument_types = _get_arguments(function)
        self.has_return = _has_return(function)
        self.return_type = _get_return_type(function)
        self.has_yield = _has_yield(function)
        self.docstring = _get_docstring(function)
        try:
            self.raises = _get_exceptions_raised(function)
        except Exception as ex:
            msg = '{}: {}'.format(self.name, ex)
            logger.debug(msg)
        self.variables = _get_all_variable_names(function)
        self.raises_assert = _raises_assert(function)


def get_function_descriptions(program):
    # type: (ast.AST) -> List[FunctionDescription]
    """Get function name, args, return presence and docstrings.

    This function should be called on the top level of the
    document (for functions), and on classes (for methods.)

    Args:
        program: The tree representing the entire program.

    Returns:
        A list of function descriptions pulled from the ast.

    """
    ret = list()  # type: List[FunctionDescription]

    methods = set(_get_all_methods(program))
    for method in methods:
        ret.append(FunctionDescription(is_method=True, function=method))

    functions = set(_get_all_functions(program)) - methods
    for function in functions:
        ret.append(FunctionDescription(is_method=False, function=function))

    return ret
