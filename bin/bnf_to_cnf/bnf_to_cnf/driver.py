import argparse
from typing import (
    Optional,
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


def main():
    args = parser.parse_args()
    driver = Driver().read(args.file[0])
    translated = (
        driver.parse().translate().validate()
    ).write(args.format)

    if args.output:
        with open(args.output[0], 'w') as fout:
            fout.write(translated)
    else:
        print(translated)


if __name__ == '__main__':
    main()
