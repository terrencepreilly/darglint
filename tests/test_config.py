"""Tests configuration scripts."""

from random import (
    choice,
    randint,
)
from string import ascii_letters
from unittest import (
    mock,
    TestCase,
)

from darglint.config import (
    walk_path,
    POSSIBLE_CONFIG_FILENAMES,
    find_config_file_in_path,
)


class WalkPathTestCase(TestCase):
    """Tests the walk_path function."""

    @mock.patch('darglint.config.os.getcwd')
    def test_at_root_yields_only_once(self, mock_getcwd):
        """We should only get root once."""
        mock_getcwd.return_value = '/'
        path_walker = walk_path()
        self.assertEqual(next(path_walker), '/')
        with self.assertRaises(StopIteration):
            next(path_walker)

    @mock.patch('darglint.config.os.getcwd')
    def test_really_long_path(self, mock_getcwd):
        directories = [
            ''.join([
                choice(ascii_letters + '_-')
                for _ in range(randint(1, 10))
            ])
            for __ in range(randint(10, 30))
        ]
        cwd = '/' + '/'.join(directories)
        mock_getcwd.return_value = cwd
        path_walker = walk_path()
        paths_walked = [x for x in path_walker]
        self.assertEqual(
            len(paths_walked),
            len(directories) + 1,
            'Should have had {} but had {} paths.'.format(
                len(directories),
                len(paths_walked) + 1,
            )
        )


class FindConfigFileInPathTestCase(TestCase):
    """Test that the config file is being found."""

    @mock.patch('darglint.config.configparser.ConfigParser')
    @mock.patch('darglint.config.os.listdir')
    def test_filename_checked(self, mock_listdir, mock_ConfigParser):
        """Check that only the necessary filenames are identified."""
        fake_files = [
            ''.join([choice(ascii_letters + '_-')
                     for _ in range(randint(5, 10))]) for _ in range(10)
        ]
        mock_listdir.return_value = (
            fake_files + list(POSSIBLE_CONFIG_FILENAMES)
        )

        config_parser = mock.MagicMock()
        mock_ConfigParser.return_value = config_parser

        contents_checked = list()

        def read_file(filename):
            contents_checked.append(filename)
            return mock.MagicMock()

        config_parser.read = read_file

        find_config_file_in_path('asonteusantoheusnth')

        self.assertEqual(
            set(contents_checked),
            set(POSSIBLE_CONFIG_FILENAMES)
        )
