import argparse
from typing import (
    Dict,
    Optional,
    Iterator,
)
from .parser import Parser
from .validate import Validator
from .translator import Translator
from .node import Node

parser = argparse.ArgumentParser(description='Convert BNF grammar to CNF')
parser.add_argument(
    'file',
    nargs=1,
    type=str,
    help=(
        'The file to read the grammar from.'
    ),
)
parser.add_argument(
    '-f',
    '--format',
    choices=['cyk', 'py'],
    default='py',
    nargs='?',
    type=str,
    help=(
        'The output format.  Can be either "cyk" or "py".  "cyk" '
        'outputs the file in CYK format, as a .cyk file.  Py '
        'generates a grammar which can be read by darglint.'
    ),
)
parser.add_argument(
    '-o',
    '--output',
    nargs=1,
    type=str,
    default=None,
    help=(
        'The output file.'
    )
)


class Driver(object):

    def __init__(self):
        self.data = None  # type: Optional[str]
        self.parser = Parser()
        self.validator = Validator()
        self.translator = Translator()
        self.tree = None  # type: Optional[Node]

    def read(self, filename: str) -> 'Driver':
        with open(filename, 'r') as fin:
            self.data = fin.read()
        return self

    def parse(self) -> 'Driver':
        self.tree = self.parser.parse(self.data)
        return self

    def translate(self) -> 'Driver':
        self.translator.translate(self.tree)
        return self

    def validate(self) -> 'Driver':
        self.validator.validate(self.tree)
        return self

    def write(self, _format: str) -> str:
        assert self.tree is not None
        if _format == 'cyk':
            return str(self.tree)
        elif _format == 'py':
            return self.tree.to_python()
        else:
            raise Exception(f'Unrecognized format type {_format}')

    def get_imports(self) -> Iterator[str]:
        assert self.tree is not None
        for _import in self.tree.filter(Node.is_import):
            assert _import.value is not None
            yield _import.value

    def merge(self, driver: 'Driver'):
        """Merge in the grammar at the given filename with this grammar.

        Args:
            driver: Another driver to merge into this one.

        """
        assert self.tree is not None
        assert driver.tree is not None
        self.tree.merge(driver.tree)


def load_script(filename: str, cache: Dict[str, Driver] = dict()):
    """Recursively load a script, parsing it and adding dependencies.

    Args:
        filename: The name of the file to open.
        cache: A cache to avoid duplicate work.

    Returns:
        The fully parsed grammar.

    """
    assert filename not in cache
    driver = Driver().read(filename).parse()
    cache[filename] = driver

    # We know that merging doesn't introduce new imports,
    # so it's safe to immediately merge subgrammars.
    for filename in driver.get_imports():
        if filename in cache:
            # We skip already imported scripts, to avoid
            # having multiple copies of the productions.
            continue
        else:
            subdriver = load_script(filename, cache)
            driver.merge(subdriver)

    return driver


def main():
    args = parser.parse_args()
    driver = load_script(args.file[0])
    translated = driver.translate().validate().write(args.format)

    if args.output:
        with open(args.output[0], 'w') as fout:
            fout.write(translated)
    else:
        print(translated)


if __name__ == '__main__':
    main()
