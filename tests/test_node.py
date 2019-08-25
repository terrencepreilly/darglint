"""Tests for the parser Node class."""

from random import (
    randint,
)
from unittest import (
    TestCase,
)

from darglint.node import (
    CykNode,
)


class CykNodeTest(TestCase):

    def build_binary_search_tree(self, root, value):
        if value < root.value:
            if not root.lchild:
                root.lchild = CykNode(symbol='', value=value)
            else:
                self.build_binary_search_tree(root.lchild, value)
        elif value > root.value:
            if not root.rchild:
                root.rchild = CykNode(symbol='', value=value)
            else:
                self.build_binary_search_tree(root.rchild, value)
        else:
            pass

    def assertIsSorted(self, arr, reverse=False):
        for i in range(len(arr) - 1):
            if reverse:
                self.assertTrue(
                    arr[i] >= arr[i + 1],
                    '{} is not sorted.'.format(arr),
                )
            else:
                self.assertTrue(
                    arr[i] <= arr[i + 1],
                    '{} is not sorted.'.format(arr),
                )

    def test_in_order_traversal(self):
        node = CykNode(symbol='', value=randint(-100, 100))
        for i in range(20):
            self.build_binary_search_tree(node, randint(-100, 100))
        values = [x.value for x in node.in_order_traverse()]
        self.assertIsSorted(values)
