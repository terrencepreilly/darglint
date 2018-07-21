"""This module reads the configuration file."""

import configparser
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


class Configuration(object):

    def __init__(self, ignore, message_template, style):
        # type: (List[str], Optional[str], DocstringStyle) -> None
        """Initialize the configuration object.

        Args:
            ignore: A list of error codes to ignore.
            message_template: the template with which to format the errors.
            style: The style of docstring.

        """
        self.ignore = ignore
        self.message_template = message_template
        self.style = style


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
    message_template = None
    style = DocstringStyle.GOOGLE
    if 'darglint' in config.sections():
        if 'ignore' in config['darglint']:
            errors = config['darglint']['ignore']
            for error in errors.split(','):
                ignore.append(error.strip())
        if 'message_template' in config['darglint']:
            message_template = config['darglint']['message_template']
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
    return Configuration(
        ignore=ignore,
        message_template=message_template,
        style=style
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
            style=DocstringStyle.GOOGLE
        )
    return load_config_file(filename)


def get_logger():  # type: () -> Logger
    """Get the default logger for darglint.

    Returns:
        The default logger for darglint.

    """
    return logger
