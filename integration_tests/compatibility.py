"""Tests for compatibility with other flake8 plugins."""

import subprocess
from unittest import TestCase


class CompatibilityTest(TestCase):
    """A simple compatibility test for Darglint.

    Currently, this test only checks for the presence of certain
    errors which we know to be present.  Ideally, we would run
    the test against a set of repositories, record the errors found,
    and make sure the same errors are found when run along with darglint.
    That may not be easy, though, since flake8 doesn't seem to have a
    command-line option to disable a particular extension.

    """

    def test_flake8_docstrings_flake8_rst_docstrings(self):
        proc = subprocess.run([
                'flake8',
                '--isolated',
                '--enable-extensions=TRUE',
                'integration_tests/files/problematic.py',
            ], stdout=subprocess.PIPE
        )
        result = proc.stdout.decode('utf8')
        print(result)

        self.assertTrue(
            'D401' in result,
            'The file should contain an error from flake8-docstrings.',
        )
        self.assertTrue(
            'RST399' in result,
            'The file should contain an error from flake8-rst-docstrings',
        )
        self.assertTrue(
            'DAR101' in result,
            'The file should contain an error from darglint.',
        )
