"""A linter for docstrings following the google docstring format."""
import sys
from typing import (
    Dict,
    List,
    Tuple,
)
from redbaron import RedBaron


def read_program(filename: str) -> str:
    """Read a program from a file."""
    program = None  # type: str
    with open(filename, 'r') as fin:
        program = fin.read()
    return program


def _get_arguments(args: List[Dict]) -> List[str]:
    argnames = list()  # type: List[str]
    for arg in args:
        if arg['type'] == 'def_argument':
            argnames.append(arg['target']['value'])
    return argnames


def _has_return(value: List[Dict]) -> bool:
    return any([x['type'] == 'return' for x in value])


def _get_docstring(value: List[Dict]) -> str:
    for node in value:
        if node['type'] == 'string':
            return node['value']
        if node['type'] not in ['endl']:
            return None
    return None


def get_functions(fst: List[Dict]) -> List[Dict]:
    """Get the functions at the given level of the program."""
    return [x for x in fst if x['type'] == 'def']


def get_methods_of_classes(fst: List[Dict]) -> List[Dict]:
    """Get the methods of the classes at this level."""
    klasses = [x for x in fst if x['type'] == 'class']
    methods = list()  # type: List[Dict]
    for klass in klasses:
        methods.extend([
            x for x in klass['value']
            if x['type'] == 'def'
        ])
    return methods


def _get_decorator_name(decorator_definition: Dict) -> str:
    is_null = decorator_definition is None
    is_decorator = decorator_definition['type'] == 'decorator'
    if is_null or not is_decorator:
        return None
    inner_definition = decorator_definition['value']
    if inner_definition['type'] != 'dotted_name':
        return None
    for subdict in inner_definition['value']:
        if subdict['type'] == 'name':
            return subdict['value']
    return None


def _is_classmethod(method: Dict) -> bool:
    return any([_get_decorator_name(dec) == 'classmethod'
                for dec in method['decorators']])


def _is_staticmethod(method: Dict) -> bool:
    return any([_get_decorator_name(dec) == 'staticmethod'
                for dec in method['decorators']])


def _get_stripped_method_args(method: Dict) -> List[str]:
    args = _get_arguments(method['arguments'])
    if 'cls' in args and _is_classmethod(method):
        args.remove('cls')
    elif 'self' in args and not _is_staticmethod(method):
        args.remove('self')
    return args


def get_functions_and_docstrings(fst: Dict) -> List[Tuple]:
    """Get function name, args, return presence and docstrings.

    This function should be called on the top level of the
    document (for functions), and on classes (for methods.)
    """
    ret = list()  # type: List[Tuple]

    functions = get_functions(fst)
    for function in functions:
        name = function['name']
        argnames = _get_arguments(function['arguments'])
        has_return = _has_return(function['value'])
        docstring = _get_docstring(function['value'])
        ret.append((name, argnames, has_return, docstring))

    methods = get_methods_of_classes(fst)
    for method in methods:
        name = method['name']
        argnames = _get_stripped_method_args(method)
        has_return = _has_return(method['value'])
        docstring = _get_docstring(method['value'])
        ret.append((name, argnames, has_return, docstring))

    return ret


def get_fst(program: str) -> List[Dict]:
    """Get the fst for this program."""
    red = RedBaron(program)
    return red.fst()


if __name__ == '__main__':
    program = read_program(sys.argv[1])
    fst = get_fst(program)
    print(get_functions_and_docstrings(fst))
