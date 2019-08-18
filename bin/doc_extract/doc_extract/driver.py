import argparse
import json
import sys
from typing import (
    Any,
    Dict,
    List,
)
import random

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
parser.add_argument(
    '-v',
    '--version',
    action='store_true',
    help=(
        'Get the version number.'
    )
)
parser.add_argument(
    '--shuffle',
    action='store_true',
    help=(
        'Shuffle the resulting docstrings.'
    ),
)


version = '0.0.1'


class Driver(object):

    def __init__(
        self,
        source: str = '',
        output: str = '',
        shuffle: bool = False,
    ):
        self.source = source
        self.output = output
        self.shuffle = shuffle

    def run(self) -> None:
        if self.source:
            try:
                with open(self.source, 'r') as fin:
                    paths = [x.strip() for x in fin.readlines()]
            except Exception as ex:
                print(f'Failed to open sourcefile {ex}')
        else:
            paths = sys.stdin.readlines()

        contents = list()  # type: List[Dict[str, Any]]

        for path in paths:
            try:
                repo = Repository(path)
                for filename in repo.python_files:
                    for docstring in extract(repo.python_files[filename]):
                        if not docstring:
                            continue
                        contents.append({
                            'filename': filename,
                            'docstring': docstring,
                            'repository': path,
                            'type': 'GOOGLE',
                            'metadata': {
                                'arguments': [],
                                'raises': [],
                                'variables': [],
                                'sections': [],
                                'noqas': [],
                            }
                        })
            except Exception as ex:
                print(f'Unable to read from {path}: {ex}', file=sys.stderr)

        if self.shuffle:
            random.shuffle(contents)

        if self.output:
            try:
                with open(self.output, 'w') as fout:
                    json.dump(contents, fout)
            except Exception as ex:
                print(f'Unable to write to output {ex}')
        else:
            print(contents, file=sys.stdout)


def main():
    args = parser.parse_args()
    if args.version:
        print(version)
        return
    try:
        Driver(
            source=args.source,
            output=args.output,
            shuffle=args.shuffle,
        ).run()
    except Exception as ex:
        print(f'Encountered error during execution: {ex}')


if __name__ == '__main__':
    main()
