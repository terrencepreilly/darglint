"""This module reads the configuration file."""

import configparser
from enum import Enum
import logging
from logging import (  # noqa
    Logger,
)
import os

from typing import (  # noqa
    Iterable,
    List,
    Optional,
)

from .docstring.base import DocstringStyle


# TODO: Configure this logger and allow the user to specify
# the whether they want warnings.
#
# All warnings will be printed at the ERROR level.
logger = logging.getLogger('darglint')

POSSIBLE_CONFIG_FILENAMES = (
    '.darglint',
    'setup.cfg',
    'tox.ini',
)

DEFAULT_DISABLED = {'DAR104'}


class Strictness(Enum):
    """The minimum strictness with which to apply checks.

    Strictness does not describe whether or not a check
    should be applied. Rather, if a check is done, strictness
    describes how intense/strict/deep the check should be.

    Each level here describes what is required of the
    docstring at the given level of strictness.  For example,
    SHORT_DESCRIPTION describes the situation where one-liners are
    allowed, and sections are not required.

    If the docstring being checked contains more than the
    allowed amount below, then it is assumed that everything
    must be checked.

    """

    # Allow a single-line description.
    SHORT_DESCRIPTION = 1

    # Allow a single-line description followed by a long
    # description, but no sections.
    LONG_DESCRIPTION = 2

    # Require everything.
    FULL_DESCRIPTION = 3


class Configuration(object):

    def __init__(self, ignore, message_template, style, strictness,
                 ignore_regex=None, enable=[], indentation=4):
        # type: (List[str], Optional[str], DocstringStyle, Strictness, Optional[str], List[str], int) -> None
        """Initialize the configuration object.

        Args:
            ignore: A list of error codes to ignore.
            message_template: the template with which to format the errors.
            style: The style of docstring.
            strictness: The minimum strictness to allow.
            ignore_regex: A regular expression which enables ignoring
                functions/methods by name.
            enable: A list of of error codes that are disabled by default.
            indentation: The number of spaces to count as an indent.

        """
        self._enable = enable
        self._ignore = ignore
        self.message_template = message_template
        self.style = style
        self.strictness = strictness
        self.errors_to_ignore = self._get_errors_to_ignore()
        self.ignore_regex = ignore_regex
        self.indentation = indentation

    @property
    def enable(self):
        # type: () -> List[str]
        return self._enable

    @enable.setter
    def enable(self, errors):
        # type: (List[str]) -> None
        self._enable = errors
        self.errors_to_ignore = self._get_errors_to_ignore()

    @property
    def ignore(self):
        # type: () -> List[str]
        return self._ignore

    @ignore.setter
    def ignore(self, errors):
        # type: (List[str]) -> None
        self._ignore = errors
        self.errors_to_ignore = self._get_errors_to_ignore()

    def _get_errors_to_ignore(self):
        # type: () -> List[str]
        """Update the errors to ignore, accounding for defaults.

        For use in constructing a cached `errors_to_ignore` value.
        Since this value could be used frequently, it makes
        sense to cache this value.

        Returns:
            The errors to ignore, including the default errors.

        """
        disabled = DEFAULT_DISABLED - set(self._enable)
        return self._ignore + list(disabled)


def load_config_file(filename):  # type: (str) -> Configuration
    """Load the config file located at the filename.

    Args:
        filename: A valid filename to read from.

    Raises:
        Exception: When the configuration style is not a valid choice.

    Returns:
        A Configuration object.

    """
    config = configparser.ConfigParser()
    config.read(filename)
    ignore = list()
    enable = list()
    message_template = None
    ignore_regex = None
    style = DocstringStyle.GOOGLE
    strictness = Strictness.FULL_DESCRIPTION
    indentation = 4
    if 'darglint' in config.sections():
        if 'ignore' in config['darglint']:
            errors = config['darglint']['ignore']
            for error in errors.split(','):
                ignore.append(error.strip())
        if 'enable' in config.sections():
            to_enable = config['darglint']['enable']
            for error in to_enable.split(','):
                enable.append(error.strip())
        if 'message_template' in config['darglint']:
            message_template = config['darglint']['message_template']
        if 'ignore_regex' in config['darglint']:
            ignore_regex = config['darglint']['ignore_regex']
        if 'docstring_style' in config['darglint']:
            raw_style = config['darglint']['docstring_style'].lower().strip()
            if raw_style == 'google':
                style = DocstringStyle.GOOGLE
            elif raw_style == 'sphinx':
                style = DocstringStyle.SPHINX
            else:
                raise Exception(
                    'Unrecognized style.  Should be one of {}'.format(
                        [x.name for x in DocstringStyle]
                    )
                )
        if 'strictness' in config['darglint']:
            raw_strictness = config['darglint']['strictness'].lower().strip()
            if raw_strictness in {'short_description', 'short'}:
                strictness = Strictness.SHORT_DESCRIPTION
            elif raw_strictness in {'long_description', 'long'}:
                strictness = Strictness.LONG_DESCRIPTION
            elif raw_strictness in {'full_description', 'full'}:
                strictness = Strictness.FULL_DESCRIPTION
            else:
                raise Exception(
                    'Unrecognized stricteness amount.  '
                    'Should be one of {"short", "long", "full"}'
                )
        if 'indentation' in config['darglint']:
            try:
                indentation = int(config['darglint']['indentation'])
            except ValueError:
                raise Exception(
                    'Unrecognized value for indentation.  Expected '
                    'a non-zero, positive integer, but received {}'.format(
                        config['darglint']['indentation']
                    )
                )
    return Configuration(
        ignore=ignore,
        message_template=message_template,
        style=style,
        strictness=strictness,
        ignore_regex=ignore_regex,
        enable=enable,
        indentation=indentation,
    )


def walk_path():  # type: () -> Iterable[str]
    """Yield directories from the current to root.

    Yields:
        The current directory, then its parent, etc. all
        the way up to root.

    """
    cwd = os.getcwd()
    yield cwd
    prev = cwd
    next_path = os.path.dirname(cwd)

    # Assumes that os.path.dirname will give the root path back
    # when given the root path.
    while prev != next_path:
        yield next_path
        prev = next_path
        next_path = os.path.dirname(next_path)


def find_config_file_in_path(path):  # type: (str) -> Optional[str]
    """Return the config path, if it is correct, or None.

    Args:
        path: The path to check.

    Returns:
        The fully qualified path to the config file, if it is
        in this directory, otherwise none.

    """
    filenames = os.listdir(path)
    for filename in filenames:
        if filename in POSSIBLE_CONFIG_FILENAMES:
            config = configparser.ConfigParser()
            fully_qualified_path = os.path.join(path, filename)
            try:
                config.read(fully_qualified_path)
                if 'darglint' in config.sections():
                    return fully_qualified_path
            except configparser.ParsingError:
                logger.error('Unable to parse file {}'.format(
                    fully_qualified_path
                ))
    return None


def find_config_file():  # type: () -> Optional[str]
    """Return the location of the config file.

    Returns:
        The location of the config file, if it exists.
        Otherwise, returns None.

    """
    # Check the current directory
    for path in walk_path():
        possible_config_filename = find_config_file_in_path(path)
        if possible_config_filename is not None:
            return possible_config_filename
    return None


def get_config():  # type: () -> Configuration
    """Locate the configuration file and return its Configuration.

    Returns:
        The Configuration described in the nearest configuration file,
        otherwise an empty Configuration.

    """
    filename = find_config_file()
    if filename is None:
        return Configuration(
            ignore=list(),
            message_template=None,
            style=DocstringStyle.GOOGLE,
            strictness=Strictness.FULL_DESCRIPTION,
        )
    return load_config_file(filename)


def get_logger():  # type: () -> Logger
    """Get the default logger for darglint.

    Returns:
        The default logger for darglint.

    """
    return logger
