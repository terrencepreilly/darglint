import argparse
import json
import sys
from typing import (
    Dict,
    List,
)

from .extract import (
    extract,
)
from .repository import (
    Repository,
)

parser = argparse.ArgumentParser(
    description='Extract docstrings from git repos.'
)
parser.add_argument(
    '-s',
    '--source',
    nargs='?',
    type=str,
    default='',
    help=(
        'The file to get repositories from.  If missing, '
        'reads from stdin.'
    )
)
parser.add_argument(
    '-o',
    '--output',
    nargs='?',
    default='',
    help=(
        'The file to place the extracted docstrings into, in '
        'JSON format.  If missing, prints to stdout.'
    )
)


class Driver(object):

    def __init__(self, source: str = '', output: str = ''):
        self.source = source
        self.output = output

    def run(self) -> None:
        if self.source:
            with open(self.source, 'r') as fin:
                paths = [x.strip() for x in fin.readlines()]
        else:
            paths = sys.stdin.readlines()

        contents = list()  # type: List[Dict[str, str]]]

        for path in paths:
            try:
                repo = Repository(path)
                for filename in repo.python_files:
                    for docstring in extract(repo.python_files[filename]):
                        contents.append({
                            'filename': filename,
                            'docstring': docstring,
                            'repository': path,
                            'metadata': {
                                'arguments': [],
                                'raises': [],
                                'variables': [],
                                'sections': [],
                            }
                        })
            except Exception as ex:
                print(f'Unable to read from {path}: {ex}', file=sys.stderr)

        if self.output:
            with open(self.output, 'w') as fout:
                json.dump(contents, fout)
        else:
            print(contents, file=sys.stdout)


def main():
    args = parser.parse_args()
    Driver(
        source=args.source,
        output=args.output,
    ).run()


if __name__ == '__main__':
    main()
