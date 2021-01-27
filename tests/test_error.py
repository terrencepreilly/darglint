import ast
from unittest import (
    skip,
    TestCase,
)

from darglint.function_description import get_function_descriptions
from darglint.integrity_checker import IntegrityChecker
from darglint.docstring.style import DocstringStyle
from darglint.strictness import Strictness
from darglint.utils import (
    ConfigurationContext,
)


class ErrorTest(TestCase):
    """Tests for the error class."""

    def get_n_errors(self, amount, src, config=dict()):
        tree = ast.parse(src)
        functions = get_function_descriptions(tree)
        with ConfigurationContext(**config):
            checker = IntegrityChecker()
            checker.run_checks(functions[0])
            errors = checker.errors
            self.assertEqual(
                len(errors),
                amount,
                (
                    'There should only be {} errors, '
                    'but there were {}: {}.'
                ).format(
                    amount,
                    len(errors),
                    ' '.join([x.__class__.__name__ for x in errors])
                )
            )
        return errors

    def get_single_error(self, src, config=dict()):
        return self.get_n_errors(1, src, config)[0]

    def test_missing_section_has_no_line_number(self):
        """Make sure missing sections can't have numbers."""
        src = '\n'.join([
            'def do_nothing(x):',
            '    """This is missing the parameter."""',
            '    pass',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            None
        )

    def test_missing_single_parameter_has_line_number(self):
        """Make sure present sections are default for missing errors."""
        src = '\n'.join([
            'def do_nothing(x, y):',
            '    """This is missing.',
            '',
            '    Args:',
            '        x: The first argument.',
            '',
            '    """',
            '    pass',
            '',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (2, 3)
        )

    def test_incorrect_parameter_has_line_number(self):
        """Make sure we point to exactly the incorrect parameter."""
        src = '\n'.join([
            'def double_x():',
            '    """Double the global x value.',
            '    ',
            '    Args:',
            '        y: The wrong parameter.',
            '',
            '    """',
            '    global x',
            '    x = 2 * x',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (3, 3),
        )

    @skip('Handle style errors!')
    def test_generic_syntax_error_has_line_number_of_last_correct(self):
        """Make sure that the syntax errors use the line number."""
        src = '\n'.join([
            'def poor_syntax():',
            '    """Raises will miss a colon.',
            '    ',
            '    Raises',
            '        Exception: This will fail.',
            '',
            '    """',
            '    raise Exception()',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (2, 2),
        )

    def test_parameter_type_mismatch_points_to_docstring_parameter(self):
        """Make sure we don't point to the function declaration."""
        src = '\n'.join([
            'def mismatched(a: int):',
            '    """Raises an error.',
            '',
            '    Args:',
            '        a (str): The wrong type.',
            '',
            '    """',
            '    print(a + " dollars.")',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (3, 3),
            'It should point to the third line.',
        )

    def test_missing_return_error_has_no_line_number(self):
        """Make sure we don't have line numbers for a missing return error."""
        src = '\n'.join([
            'def missing_return():',
            '    """Get the item."""',
            '    global item',
            '    return item',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            None,
            'There should be no line numbers.'
        )

    def test_excess_return_error_points_to_returns_section(self):
        """Make sure the excess return error points to the returns section."""
        src = '\n'.join([
            'def double_item():',
            '    """Double the item.',
            '',
            '    Returns:',
            '        Actually Nothing.',
            '',
            '    """',
            '    global item',
            '    item *= 2',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (2, 3),
            'It should point to the return section head.',
        )

    def test_return_type_mismatch_error_points_to_returns_section(self):
        """Make sure the type mismatch error points the type."""
        src = '\n'.join([
            'def double(x: int) -> int:',
            '    """Dobule the value given.',
            '',
            '    Args:',
            '        x (int): A value to double.',
            '',
            '    Returns:',
            '        str: The value to double.',
            '',
            '    """',
            '    return x * 2',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (5, 6),
            'It should point to the type.',
        )

    def test_missing_yield_error_has_no_line_number(self):
        """Make sure we don't have line numbers for a missing yield error."""
        src = '\n'.join([
            'def missing_return():',
            '    """Get the item."""',
            '    global items',
            '    for item in items:',
            '        yield item',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            None,
            'There should be no line numbers.'
        )

    def test_excess_yield_error_points_to_yields_section(self):
        """Make sure the excess yield error points to the returns section."""
        src = '\n'.join([
            'def double_item():',
            '    """Double the item.',
            '',
            '    Yields:',
            '        Actually Nothing.',
            '',
            '    """',
            '    global item',
            '    item *= 2',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (2, 3),
            'It should point to the yield section head.',
        )

    def test_missing_raise_error_has_no_line_number(self):
        """Make sure we don't have line numbers for a missing raise error."""
        src = '\n'.join([
            'def missing_raises():',
            '    """Get the item."""',
            '    raise Exception("Finish me!")',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            None,
            'There should be no line numbers.'
        )

    def test_excess_raise_error_points_to_item(self):
        """Make sure the excess raise error points to the excess item."""
        src = '\n'.join([
            'def double_item():',
            '    """Double the item.',
            '',
            '    Raises:',
            '        Exception: Actually Nothing.',
            '',
            '    """',
            '    global item',
            '    item *= 2',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (3, 3),
            'It should point to the Excess item..',
        )

    @skip('Handle style errors!')
    def test_missing_definition_after_item_points_to_item_line(self):
        """Make sure empty definitions point to lines."""
        src = '\n'.join([
            'def missing_definition(x):',
            '    """Missing the definition.',
            '',
            '    Args:',
            '        x:',
            '',
            '    """',
            '    print(x)',
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (3, 3),
            'It should point to the item\'s line.'
        )

    @skip('Handle style errors!')
    def test_missing_definition_points_to_items_in_middle(self):
        """Make sure it works if the empty description is in the middle."""
        src = '\n'.join([
            'def missing_def(x, y, z):',
            '    """Missing a single one.',
            '',
            '    Args:',
            '        x: The first.',
            '        y:',
            '        z: Something else.',
            '',
            '    """',
            '    print(x + y + z)'
        ])
        error = self.get_single_error(src)
        self.assertEqual(
            error.line_numbers,
            (4, 4),
            'It should point to the item line.',
        )

    def test_default_disabled_error(self):
        not_enabled_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.FULL_DESCRIPTION,
            'enable': [],
        }
        enabled_config = {
            'ignore': [],
            'message_template': None,
            'style': DocstringStyle.GOOGLE,
            'strictness': Strictness.FULL_DESCRIPTION,
            'enable': ['DAR104'],
        }
        src = '\n'.join([
            'def double(x):',
            '    """Double the value.',
            '    ',
            '    Args:',
            '        x: The value to double.',
            '',
            '    Returns:',
            '        The value, doubled.',
            '',
            '    """',
            '    return 2 * x',
        ])

        errors = self.get_n_errors(0, src, not_enabled_config)
        self.assertEqual(
            len(errors),
            0,
        )

        errors = self.get_n_errors(1, src, enabled_config)
        self.assertEqual(
            len(errors),
            1,
        )

    def test_ignore_raise(self):
        ignore_raise_config = {
            'ignore_raise': ['ValueError']
        }
        src = '\n'.join([
            'def undocumented_exception():',
            '    """Make sure ignore_raise works correctly."""',
            '    raise ValueError',
        ])

        errors = self.get_n_errors(1, src)
        self.assertEqual(
            len(errors),
            1,
        )

        errors = self.get_n_errors(0, src, ignore_raise_config)
        self.assertEqual(
            len(errors),
            0,
        )
