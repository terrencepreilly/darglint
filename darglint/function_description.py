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

from .analysis.analysis_visitor import (
    AnalysisVisitor,
)
from .analysis.function_and_method_visitor import (
    FunctionAndMethodVisitor,
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


def _is_staticmethod(fun):  # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> bool  # noqa: E501
    return 'staticmethod' in _get_decorator_names(fun)


def _get_return_type(fn):
    # type: (Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]
    if fn.returns is not None and hasattr(fn.returns, 'id'):
        return getattr(fn.returns, 'id')
    return None


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
        visitor = AnalysisVisitor()
        try:
            visitor.visit(function)
        except Exception as ex:
            msg = 'Failed to visit in {}: {}'.format(self.name, ex)
            logger.debug(msg)
            return
        self.argument_names = visitor.arguments
        self.argument_types = visitor.types
        if is_method and len(self.argument_names) > 0:
            if not _is_staticmethod(function):
                self.argument_names.pop(0)
                self.argument_types.pop(0)
        self.has_return = bool(visitor.returns)
        self.has_empty_return = self.has_return and visitor.returns[0].value is None
        self.return_type = _get_return_type(function)
        self.has_yield = bool(visitor.yields)
        self.raises = visitor.exceptions
        self.docstring = _get_docstring(function)
        self.variables = [x.id for x in visitor.variables]
        self.raises_assert = bool(visitor.asserts)


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

    visitor = FunctionAndMethodVisitor()
    visitor.visit(program)
    for method in visitor.methods:
        ret.append(FunctionDescription(is_method=True, function=method))

    for function in visitor.functions:
        ret.append(FunctionDescription(is_method=False, function=function))

    return ret
