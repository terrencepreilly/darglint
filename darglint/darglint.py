"""A linter for docstrings following the google docstring format."""
import ast
from typing import (
    List,
    Iterator,
)


def read_program(filename: str) -> str:
    """Read a program from a file.

    Args:
        filename: The name of the file to read.

    Returns:
        The program as a single string.

    """
    program = None  # type: str
    with open(filename, 'r') as fin:
        program = fin.read()
    return program


def _get_arguments(fn: ast.FunctionDef) -> List[str]:
    ret = list()  # type: List[str]
    for arg in fn.args.args:
        ret.append(arg.arg)
    return ret


def _has_return(fun: ast.FunctionDef) -> bool:
    """Return true if the function has a fruitful return."""
    for node in ast.walk(fun):
        if isinstance(node, ast.Return) and node.value is not None:
            return True
    return False


def _get_docstring(fun: ast.AST) -> str:
    return ast.get_docstring(fun)


def _get_all_functions(tree: ast.AST) -> Iterator[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            yield node


def _get_all_classes(tree: ast.AST) -> Iterator[ast.ClassDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _get_all_methods(tree: ast.AST) -> Iterator[ast.FunctionDef]:
    for klass in _get_all_classes(tree):
        for fun in _get_all_functions(klass):
            yield fun


def _get_decorator_names(fun: ast.FunctionDef) -> List[str]:
    return [x.id for x in fun.decorator_list]


def _is_classmethod(fun: ast.FunctionDef) -> bool:
    return 'classmethod' in _get_decorator_names(fun)


def _is_staticmethod(fun: ast.FunctionDef) -> bool:
    return 'staticmethod' in _get_decorator_names(fun)


def _get_stripped_method_args(method: ast.FunctionDef) -> List[str]:
    args = _get_arguments(method)
    if 'cls' in args and _is_classmethod(method):
        args.remove('cls')
    elif 'self' in args and not _is_staticmethod(method):
        args.remove('self')
    return args


class FunctionDescription(object):
    """Describes a function or method."""

    def __init__(self, is_method: bool, function: ast.FunctionDef):
        """Create a new FunctionDescription.

        Args:
            is_method: True if this is a method. Will attempt to remove
                self or cls if appropriate.
            function: The base node of the function.

        """
        self.is_method = is_method
        self.function = function
        self.line_number = function.lineno
        self.name = function.name
        if is_method:
            self.argument_names = _get_stripped_method_args(function)
        else:
            self.argument_names = _get_arguments(function)
        self.has_return = _has_return(function)
        self.docstring = _get_docstring(function)


def get_function_descriptions(
        ast: ast.AST) -> List[FunctionDescription]:
    """Get function name, args, return presence and docstrings.

    This function should be called on the top level of the
    document (for functions), and on classes (for methods.)

    Args:
        ast: The tree representing the entire program.
            This should be the direct result of

    """
    ret = list()  # type: List[FunctionDescription]

    methods = set(_get_all_methods(ast))
    for method in methods:
        ret.append(FunctionDescription(is_method=True, function=method))

    functions = set(_get_all_functions(ast)) - methods
    for function in functions:
        ret.append(FunctionDescription(is_method=False, function=function))

    return ret
