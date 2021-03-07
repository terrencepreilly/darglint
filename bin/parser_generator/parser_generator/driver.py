import argparse
from itertools import chain

from .generators import generate_parser


parser = argparse.ArgumentParser(description='Generate a parser.')
parser.add_argument(
    'source',
    metavar='FILE',
    action='store',
    type=str,
    help='The file containing the grammar description.',
)
parser.add_argument(
    '--imports',
    '-i',
    nargs='*',
    action='append',
    type=str,
    help='The imports to prepend to the parser. '
    'This allows the grammar to use a user-supplied token/node definition. '
    'The objects `Token`, `TokenType`, and `Node` should be imported.'
)
parser.add_argument(
    '--lookahead',
    '-k',
    action='store',
    type=int,
    help='The k-value for the LL(K) grammar.',
)


def main():
    args = parser.parse_args()
    with open(args.source, 'r') as fin:
        grammar = fin.read()
    if args.imports:
        imports = '\n'.join(chain(*args.imports))
    else:
        imports = ''
    if args.lookahead:
        k = args.lookahead
    else:
        k = 1
    parser_repr = generate_parser(grammar, imports, k)
    print(parser_repr)


if __name__ == '__main__':
    main()
