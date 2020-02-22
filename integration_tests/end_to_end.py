from unittest import TestCase

import subprocess


class EndToEndTest(TestCase):

    def get_errors(self, filename, *args):
        invocation = ['darglint', *args]
        invocation.append(filename)
        proc = subprocess.run(
            invocation,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = proc.stdout.decode('utf8')
        return result

    def test_enable_disabled_by_default(self):
        errors = self.get_errors(
            'integration_tests/files/missing_arg_type.py',
            '--enable',
            'DAR104',
        )
        self.assertTrue('DAR104' in errors, errors)

    def test_two_space_indent(self):
        errors = self.get_errors(
            'integration_tests/files/two_spaces.py',
            '--indentation',
            '2',
        )
        self.assertEqual(errors.count('DAR101'), 1)

    def test_docstring_style_selection(self):
        for style in ['google', 'sphinx', 'numpy']:
            filename = 'integration_tests/files/{}_example.py'.format(
                style
            )
            errors = self.get_errors(
                filename,
                '--docstring-style',
                style,
            )
            self.assertEqual(
                errors.count('DAR101'),
                1,
                'Expected {} to have one missing parameter.'.format(
                    filename,
                )
            )
            self.assertEqual(
                errors.count('DAR102'),
                1,
                'Expected {} to have one extra parameter.'.format(
                    filename,
                )
            )
