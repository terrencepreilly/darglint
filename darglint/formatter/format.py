import sys

from grammar import HexNumberGrammar

from darglint.token import (
    Token,
    TokenType,
)
from darglint.parse.cyk import (
    parse,
)


# Darglint already has a lexer, but it's custom to darglint.
# For this example, I've made a small lexer.
def lex(contents):
    tokens = list()
    line_number = 1
    for c in contents:
        if c.isdigit() or c in 'abcdefABCDEF':
            tokens.append(Token(
                value=c,
                token_type=TokenType.DIGIT,
                line_number=line_number,
            ))
        elif c == '\n':
            tokens.append(Token(
                value=c,
                token_type=TokenType.NEWLINE,
                line_number=line_number,
            ))
            line_number += 1
        elif c.isspace():
            tokens.append(Token(
                value=c,
                token_type=TokenType.SPACE,
                line_number=line_number,
            ))
        elif c in {'x', 'X'}:
            if tokens[-1].value == '0':
                prev = tokens.pop().value
                tokens.append(Token(
                    value=prev + c,
                    token_type=TokenType.NUMBER_PREFIX,
                    line_number=line_number,
                ))
            else:
               tokens.append(Token(
                   value=c,
                   token_type=TokenType.INVALID,
                   line_number=line_number,
               ))
        else:
            tokens.append(Token(
                value=c,
                token_type=TokenType.INVALID,
                line_number=line_number,
            ))
    return tokens



def fix_tree(tree):
    # type: (CykNode) -> CykNode
    """Fix all errors in the tree that we can fix.

    Goes through each node in the tree, and if there is a
    fixable error, replaces it with the fixed version.

    """
    def _fix(node):
        new_node = node
        for annotation in node.annotations:
            if hasattr(annotation, 'fix'):
                new_node = annotation.fix(new_node) or new_node
        return new_node

    # We need a reference to the parent in order to replace
    # the child, so we check children first.
    for node in tree.walk():
        if node.lchild:
            node.lchild = _fix(node.lchild)
        if node.rchild:
            node.rchild = _fix(node.rchild)

    # Since the root has no parent, we just want to replace the
    # root if it has any errors.
    return _fix(tree)



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: format.py <filename>', file=sys.stderr)
    filename = sys.argv[1]
    with open(filename, 'r') as fin:
        data = fin.read().strip()

    tree = parse(HexNumberGrammar, lex(data))

    # Fixes any errors in the tree.  If there is a missing
    # or wrong token, for example, simply reconstructing the
    # string from the tree will reproduce the error.  If we
    # transform the tree first, we can fix the error.
    tree = fix_tree(tree)

    # Fixes any whitespace formatting in the tree.  This is
    # useful for when there is no complex transformation which
    # has to occur.  For example, if we want to only allow at
    # most one or two newlines.  We can't do complex transformations
    # here.
    representation = tree.reconstruct_string()

    print(representation)
