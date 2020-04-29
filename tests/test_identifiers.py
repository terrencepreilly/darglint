from unittest import TestCase
import random

from darglint.parse.identifiers import (
    Path,
)
from darglint.node import (
    CykNode,
)
from darglint.token import (
    Token,
    TokenType,
)


# The below methods made defining children
# much more concise for tests.
def _l(node):
    return CykNode(
        'left',
        lchild=node,
    )


def _r(node):
    return CykNode(
        'right',
        rchild=node
    )


target = 'target'


def _v():
    return CykNode(
        'value',
        value=Token(target, TokenType.WORD, 0)
    )


class PathTestCase(TestCase):

    def test_straight_path_passing(self):
        path = Path.of('lrv')
        node = _l(_r(_v()))
        self.assertEqual(
            path.extract(node),
            target,
        )

    def test_straight_path_failing(self):
        path = Path.of('rv')
        node = _l(_v())
        self.assertEqual(
            path.extract(node),
            None,
        )

    def test_branch_passing(self):
        path = Path.branch(Path.if_left('lrv'), Path.of('rrv'))
        left = _l(_r(_v()))
        self.assertEqual(
            path.extract(left),
            target,
        )

        right = _r(_r(_v()))
        self.assertEqual(
            path.extract(right),
            target,
        )

    def test_branch_failing(self):
        path = Path.branch(Path.if_left('lv'), Path.of('rlv'))
        node = _l(_r(_v()))
        self.assertEqual(
            path.extract(node),
            None,
        )

    def test_straight_then_branch_passing(self):
        path = Path.of('l').branch(Path.if_left('lv'), Path.if_right('rv'))
        left = _l(_l(_v()))
        self.assertEqual(
            path.extract(left),
            target,
        )

        right = _l(_r(_v()))
        self.assertEqual(
            path.extract(right),
            target,
        )

    def test_straight_then_branch_failing(self):
        path = Path.of('l').branch(Path.if_left('lv'), Path.if_right('rv'))
        node1 = _r(_v())
        node2 = _l(_l(_l(_v())))
        for i, node in enumerate([node1, node2]):
            self.assertEqual(
                path.extract(node),
                None,
                'Unexpectedly succeeded for {}'.format(i + 1),
            )

    def test_chain_is_distributive(self):
        node = _l(_l(_r(_l(_v()))))
        path1 = Path.of('llrlv')
        path2 = Path.of('llr').of('lv')
        path3 = Path.of('ll').of('rl').of('v')
        path4 = Path.of('l').of('l').of('r').of('l').of('v')
        for i, path in enumerate([path1, path2, path3, path4]):
            self.assertEqual(
                path.extract(node),
                target,
                'Failed to extract for path {}'.format(i + 1),
            )

    def test_can_extract_non_leaf(self):
        node = _l(_r(_v()))
        path = Path.of('lr')
        found = path.extract(node)
        self.assertTrue(
            isinstance(found, CykNode)
        )
        self.assertEqual(
            found.symbol,
            'value',
        )

    def _random_node(self, minlength=1, maxlength=100):
        curr = _v()
        path = 'v'
        for i in range(random.randint(minlength, maxlength)):
            c = random.choice('rl')
            path = c + path
            if c == 'r':
                curr = _r(curr)
            elif c == 'l':
                curr = _l(curr)
        return curr, path

    def _random_branch(self, curr, depth=3):
        subpaths = list()
        for _ in range(depth):
            subpath = self._random_path(depth=depth-1)
            subpaths.append(subpath)
        curr.branch(*subpaths)

    def _random_of(self, curr, depth=3):
        path = ''.join([
            random.choice('lr') for _ in range(random.randint(1, 4))
        ])
        curr.of(path)
        self._random_branch_or_of(curr, depth - 1)

    def _random_branch_or_of(self, curr, depth=3):
        if random.random() < 0.5:
            self._random_of(curr, depth)
        else:
            self._random_branch(curr, depth)

    def _random_path(self, depth=3):
        curr = Path.of('')
        self._random_branch_or_of(curr, depth=depth)
        return curr

    def test_does_not_throw_exception_passing(self):
        for _ in range(100):
            node, path_raw = self._random_node()
            path = Path.of(path_raw)
            self.assertEqual(
                path.extract(node),
                target,
            )

    def test_probably_failing_paths_dont_raise_exception(self):
        for _ in range(100):
            node = self._random_node()
            path = self._random_path(depth=3)
            path.extract(node)
