"""A linter for docstrings following the google docstring format."""
import sys
from typing import (
    Dict,
    List,
    Tuple,
)
from redbaron import RedBaron


def read_program(filename):
    """Read a program from a file."""
    program = None
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
    # TODO
    return True


def _get_docstring(value: List[Dict]) -> str:
    for node in value:
        if node['type'] == 'string':
            return node['value']
        if node['type'] not in ['endl']:
            return None
    return None


def get_functions_and_docstrings(fst: Dict) -> List[Tuple]:
    """Get function name, args, return presence and docstrings.

    This function should be called on the top level of the
    document (for functions), and on classes (for methods.)
    """
    ret = list()  # type: List[Tuple]
    functions = [x for x in fst if x['type'] == 'def']
    for function in functions:
        name = function['name']
        argnames = _get_arguments(function['arguments'])
        has_return = _has_return(function['value'])
        docstring = _get_docstring(function['value'])
        ret.append((name, argnames, has_return, docstring))
    return ret


if __name__ == '__main__':
    program = read_program(sys.argv[1])
    red = RedBaron(program)
    print(get_functions_and_docstrings(red.fst()))
