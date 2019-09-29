from unittest import TestCase
import subprocess


class SourceFileTestCase(TestCase):

    def assertWorks(self, filename):
        proc = subprocess.run([
            'darglint', filename
        ])
        self.assertTrue(
            proc.returncode in {0, 1},
            'Expected error code 0 or 1, but got {} for {}'.format(
                proc.returncode,
                filename,
            )
        )

    def test_encoding_works(self):
        for encoding in [
            'ascii',
            'utf8',
            'latin1',
        ]:
            self.assertWorks('integration_tests/files/example-{}.py'.format(
                encoding
            ))
