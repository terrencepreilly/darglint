from unittest import TestCase

from parser_generator.generators import (
    SubProduction,
)


class SubProductionTests(TestCase):

    def test_subproduction_is_iterable(self):
        sub = SubProduction(list('abc'))
        self.assertEqual(
            list(sub),
            ['a', 'b', 'c'],
        )
