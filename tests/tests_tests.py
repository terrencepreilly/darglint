import unittest


class TestTestCase(unittest.TestCase):

    def test_fails(self):
        self.fail('This test should fail with a message.')
