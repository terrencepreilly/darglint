"""Tests for the error reporting class."""

import ast
from unittest import TestCase

from darglint.error_report import ErrorReport
from darglint.errors import EmptyDescriptionError
from darglint.function_description import get_function_descriptions

def _get_function_description(program):
    tree = ast.parse(program)
    return get_function_descriptions(tree)[0]


class ErrorReportMessageTemplateTest(TestCase):
    """Test the ErrorReport templating.

    The message formatting syntax and variable names is
    taken primarily from pylint.  That will allow any users
    familiar with pylint to use this utility with some ease.
    Format strings are also very intuitive for Pythonistas.

    """

    def setUp(self):
        """Make a generic function to raise errors about."""
        self.function_description = _get_function_description('\n'.join([
            'def top_level_function(arg):',
            '    """My docstring.',
            '',
            '    Args:',
            '        arg:',
            '',
            '    """',
            '    return 1',
        ]))

        # Give a line number so that it can be sorted.
        self.function_description.lineno = 0

    def test_message_template_can_be_empty(self):
        """Ensure the error report representation can be empty."""
        message = 'Discard me.'
        error = EmptyDescriptionError(
            self.function_description, message,
        )
        filename = '/Some/File/Discarded.py'
        message_template = ''
        error_report = ErrorReport(
            errors=[error],
            filename=filename,
            message_template=message_template,
        )
        self.assertEqual(
            str(error_report), ''
        )

    def test_format_string_only_msg_id(self):
        """Ensure that message template can have one item."""
        message = 'This message is missing a description.'
        error = EmptyDescriptionError(
            self.function_description, message,
        )
        filename = '/Users/ronald_vermillion/great_donuts.ijs'
        message_template = '{msg_id}'
        error_report = ErrorReport(
            errors=[error],
            filename=filename,
            message_template=message_template
        )
        self.assertEqual(
            str(error_report),
            EmptyDescriptionError.error_code
        )

    def test_format_can_include_string_constants(self):
        """Ensure that string constants can be in message."""
        message = 'The Message!'
        error = EmptyDescriptionError(
            self.function_description, message,
        )
        filename = './some_filename.py'
        message_template = '({msg}) :)'
        error_report = ErrorReport(
            errors=[error],
            filename=filename,
            message_template=message_template
        )
        self.assertEqual(
            str(error_report),
            '(Empty description: e The Message!) :)'
        )

    def test_all_attributes(self):
        """Test against all possible attributes."""
        message = 'The Message!'
        error = EmptyDescriptionError(
            self.function_description, message,
        )
        filename = './some_filename.py'
        message_template = ' '.join([
            '{msg}',
            '{msg_id}',
            '{line}',
            '{path}',
            '{obj}',
        ])
        error_report = ErrorReport(
            errors=[error],
            filename=filename,
            message_template=message_template,
        )

        # This will raise an error if the template
        # parameters are incorrect.
        str(error_report)

    def test_message_template_is_none_uses_default(self):
        message = 'My Message'
        error = EmptyDescriptionError(
            self.function_description, message,
        )
        filename = './data/datum.py'
        error_report = ErrorReport(
            errors=[error],
            filename=filename,
            message_template=None,
        )
        error_repr = str(error_report)
        self.assertTrue(
            all([
                message in error_repr,
                filename in error_repr,
                EmptyDescriptionError.error_code in error_repr,
            ])
        )
