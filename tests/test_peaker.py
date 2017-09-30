from itertools import cycle
from unittest import TestCase

from darglint.peaker import Peaker


class PeakerTestCase(TestCase):

    def test_peak_doesnt_move_stream_forward(self):
        generator = cycle('abc')
        peaker = Peaker(stream=generator)
        self.assertEqual(peaker.peak(), 'a')
        self.assertEqual(peaker.peak(), 'a')

    def test_next_does_move_stream_forward(self):
        generator = cycle('abc')
        peaker = Peaker(stream=generator)
        self.assertEqual(peaker.next(), 'a')
        self.assertEqual(peaker.next(), 'b')

    def test_stop_iteration_raised(self):
        peaker = Peaker((x for x in 'ab'))
        self.assertEqual(peaker.next(), 'a')
        self.assertEqual(peaker.next(), 'b')
        with self.assertRaises(StopIteration):
            peaker.next()

    def test_has_next_returns_false_at_end_of_iteration(self):
        peaker = Peaker((x for x in 'ab'))
        self.assertTrue(peaker.has_next())
        peaker.next()
        self.assertTrue(peaker.has_next())
        peaker.next()
        self.assertFalse(peaker.has_next())

    def test_empty_stream_says_it_has_none(self):
        peaker = Peaker((x for x in ''))
        self.assertFalse(peaker.has_next())

    def test_take_while(self):
        peaker = Peaker((x for x in 'name    1234'))
        name = ''.join(peaker.take_while(str.isalpha))
        self.assertEqual(name, 'name')
        self.assertTrue(peaker.has_next())
        spaces = ''.join(peaker.take_while(str.isspace))
        self.assertEqual(spaces, '    ')
        self.assertTrue(peaker.has_next())
        numbers = ''.join(peaker.take_while(str.isdecimal))
        self.assertEqual(numbers, '1234')
        self.assertFalse(peaker.has_next())

    def test_passing_none_to_peaker_marks_empty(self):
        peaker = Peaker((x for x in []))
        self.assertFalse(peaker.has_next())
