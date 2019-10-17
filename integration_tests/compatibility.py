"""Tests for compatibility with other flake8 plugins."""

import subprocess
from unittest import TestCase

# Regression introduced by flake8 in 3.3.0
# Bad:  3.3.0

class CompatibilityTest(TestCase):

    def test_flake8_docstrings(self):
        proc = subprocess.run([
                'flake8',
                '--isolated',
                '--enable-extensions=TRUE',
                'integration_tests/files/example-ascii.py',
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
