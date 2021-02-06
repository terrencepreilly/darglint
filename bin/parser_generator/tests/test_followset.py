from copy import copy
from functools import reduce
from unittest import TestCase

from parser_generator.generators import (
    FollowSet,
    SubProduction,
)


class FollowSetTests(TestCase):

    def test_is_complete_only_if_no_partials(self):
        # Empty is a special case, because it doesn't represent a
        # value in and of itself -- it's the lack of a value.
        empty = FollowSet.empty('A', 1)
        self.assertTrue(empty.is_complete)

        partial = FollowSet.partial([SubProduction(['a'])], 'A', 2)
        self.assertFalse(partial.is_complete)

        complete = FollowSet.complete(
            [SubProduction(['a'])],
            'A',
            1,
        )
        self.assertTrue(complete.is_complete)

        initially_complete = complete
        initially_complete.upgrade(partial)
        self.assertFalse(initially_complete.is_complete)

    def test_create_empty_followset(self):
        partial = FollowSet.empty('A', 1)
        self.assertTrue(partial.is_complete)
        self.assertEqual(partial.partials, [])
        self.assertEqual(partial.k, 1)
        self.assertEqual(partial.follow, 'A')

    def test_upgrade_followset_adopts_k_and_partial(self):
        partial = FollowSet.empty('A', 1)
        other = FollowSet.partial([SubProduction(list('ab'))],'A', 3)
        partial.upgrade(other)
        self.assertEqual(partial.k, other.k)
        self.assertEqual(partial.partials, other.partials)

    def test_upgrade_retains_additional(self):
        complete = FollowSet.complete([SubProduction(list('ab'))], 'A', 2)
        partial = FollowSet.empty('A', 3)
        prev = copy(complete.additional)
        complete.upgrade(partial)
        self.assertEqual(
            complete.additional,
            prev,
        )

    def test_upgrade_retains_partials(self):
        partial = FollowSet.partial([SubProduction(['a'])], 'A', 2)
        other = FollowSet.partial([SubProduction(list('bc'))], 'A', 3)
        partial.upgrade(other)
        self.assertEqual(
            partial.partials,
            [
                SubProduction(['a']),
                SubProduction(['b', 'c']),
            ],
        )

    def test_upgrade_retains_complete(self):
        complete = FollowSet.complete([SubProduction(['a'])], 'A', 1)
        other = FollowSet.complete([SubProduction(list('bc'))], 'A', 2)
        complete.upgrade(other)
        self.assertEqual(
            complete.completes,
            [
                SubProduction(['a']),
                SubProduction(['b', 'c']),
            ],
        )

    def test_upgrade_can_be_used_in_reduce(self):
        leftmost = FollowSet.empty('S', 1)
        followsets = [
            leftmost,
            FollowSet.partial([SubProduction(['a'])], 'S', 2),
            FollowSet.complete([SubProduction(list('bc'))], 'S', 2),
        ]

        result = reduce(FollowSet.upgrade, followsets)

        self.assertTrue(
            result == leftmost,
            'The result should be the same as the first instance in the list.'
        )
        self.assertEqual(
            result.completes,
            [SubProduction(['b', 'c'])],
        )
        self.assertEqual(
            result.partials,
            [SubProduction(['a'])],
        )
        self.assertEqual(
            result.follow,
            'S',
        )

    def test_create_a_partial_followset(self):
        partial = FollowSet.partial(
            [SubProduction(list('ab'))],
            'A',
            3,
        )
        self.assertFalse(partial.is_complete)
        self.assertEqual(partial.partials, [SubProduction(['a', 'b'])])
        self.assertEqual(partial.k, 3)
        self.assertEqual(partial.follow, 'A')

    def test_create_a_complete_followset(self):
        complete = FollowSet.complete(
            [SubProduction(list('abc'))],
            'A',
            3,
        )
        self.assertTrue(complete.is_complete)
        self.assertEqual(complete.completes, [SubProduction(['a', 'b', 'c'])])
        self.assertEqual(complete.k, 3)

    def test_cannot_append_to_a_complete_followset(self):
        complete = FollowSet.complete(
            [SubProduction(list('abc'))],
            'A',
            3,
        )
        other = FollowSet.complete(
            [SubProduction(list('def'))],
            'A',
            3,
        )
        with self.assertRaises(Exception):
            complete.append(other)

    def test_upgrade_to_other_follow_fails(self):
        partial = FollowSet.partial(
            [SubProduction(['a'])],
            'A',
            2,
        )
        wrong_follow = FollowSet.partial(
            [SubProduction(['b', 'c'])],
            'B',
            3,
        )
        with self.assertRaises(Exception):
            partial.upgrade(wrong_follow)
        self.assertEqual(partial.k, 2)

        correct_follow = FollowSet.partial(
            [SubProduction(['b', 'c'])],
            'A',
            3,
        )
        partial.upgrade(correct_follow)
        self.assertEqual(
            partial.k,
            3,
        )

    def test_append_from_partial(self):
        partial = FollowSet.partial(
            [SubProduction(list('a'))],
            'A',
            2,
        )
        other = FollowSet.partial(
            [SubProduction(list('b'))],
            'B',
            2,
        )
        partial.append(other)
        self.assertEqual(
            partial.additional,
            {SubProduction(list('ab'))},
        )

    def test_append_from_complete(self):
        partial = FollowSet.partial(
            [SubProduction(list('abc'))],
            'A',
            4,
        )
        other = FollowSet.complete(
            [SubProduction(list('defg'))],
            'A',
            4,
        )
        partial.append(other)
        self.assertEqual(
            partial.additional,
            {SubProduction(list('abcd'))}
        )

    def test_append_from_derived(self):
        partial = FollowSet.partial(
            [SubProduction(list('a'))],
            'A',
            3,
        )
        other = FollowSet.partial(
            [SubProduction(['b'])],
            'B',
            3
        )
        other.append(FollowSet.complete(
            [SubProduction(list('cde'))],
            'A',
            3,
        ))
        partial.append(other)
        self.assertEqual(
            partial.additional,
            {SubProduction(list('abc'))},
        )

    def test_changed_if_solution_added(self):
        partial = FollowSet.partial(
            [SubProduction(['a'])],
            'A',
            2,
        )
        other = FollowSet.complete(
            [SubProduction(list('bc'))],
            'A',
            2,
        )
        self.assertFalse(partial.changed)
        partial.append(other)
        self.assertTrue(partial.changed)
        partial.changed = False
        self.assertFalse(partial.changed)
        partial.append(other)
        self.assertFalse(partial.changed)
