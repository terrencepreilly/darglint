from unittest import TestCase
from unittest.mock import (
    patch,
    Mock,
)

from darglint.custom_assert import (
    Assert,
)
from darglint.config import (
    AssertStyle,
)
from darglint.utils import (
    ConfigurationContext,
)


class AssertTestCase(TestCase):

    def test_can_configure_to_raise(self):
        with ConfigurationContext(
            assert_style=AssertStyle.RAISE,
        ):
            message = 'My Message'
            with self.assertRaises(AssertionError) as exc:
                Assert(False, message)
            self.assertTrue(message in str(exc.exception))

    @patch('darglint.custom_assert.get_logger')
    def test_logs_by_default(self, mock_get_logger):
        mock_logger = Mock()
        mock_logger.error = Mock()
        mock_get_logger.return_value = mock_logger
        message = 'My Message'
        with ConfigurationContext():
            Assert(False, message)
        self.assertTrue(mock_logger.error.called)
        self.assertEqual(
            mock_logger.error.call_args[0][0],
            message,
        )
