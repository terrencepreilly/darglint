"""A module to read/define configuration and logging.

This module contains two global instances which should
be accessed only through their getter/setter methods.
These instances are not threadsafe: they should be
updated only prior to spawning any threads.

"""

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

try:
    import tomli
except ImportError:
    _has_tomli = False
else:
    _has_tomli = True

from .docstring.style import DocstringStyle
from .strictness import Strictness


def get_logger():  # type: () -> Logger
    """Get the default logger for darglint.

    Returns:
        The default logger for darglint.

    """
    return logging.getLogger('darglint')


POSSIBLE_CONFIG_FILENAMES = (
    '.darglint',
    'setup.cfg',
    'tox.ini',
    'pyproject.toml',
)

DEFAULT_DISABLED = {'DAR104'}


class AssertStyle(Enum):
    """Describes how to handle assertions."""
    RAISE = 1
    LOG = 2


class LogLevel(Enum):
    """Describes the level of error which should be logged.

    These levels correspond to the levels in logging.
    This wrapper primarily serves as a means of conveniently
    parsing the levels, while maintaining the same interface
    as other options.

    """
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @classmethod
    def from_string(cls, level):
        # type: (str) -> LogLevel
        normalized_level = level.lower().strip()
        if normalized_level == 'critical':
            return cls.CRITICAL
        elif normalized_level == 'error':
            return cls.ERROR
        elif normalized_level == 'warning':
            return cls.WARNING
        elif normalized_level == 'info':
            return cls.INFO
        elif normalized_level == 'debug':
            return cls.DEBUG
        else:
            raise ValueError('Unrecognized log level, "{}"'.format(
                level
            ))


class Configuration(object):

    def __init__(self, ignore, message_template, style, strictness,
                 ignore_regex=None, ignore_raise=[], ignore_properties=False, enable=[],
                 indentation=4, assert_style=AssertStyle.LOG,
                 log_level=LogLevel.CRITICAL):
        # type: (List[str], Optional[str], DocstringStyle, Strictness, Optional[str], List[str], bool, List[str], int, AssertStyle, LogLevel) -> None  # noqa: E501
        """Initialize the configuration object.

        Args:
            ignore: A list of error codes to ignore.
            message_template: the template with which to format the errors.
            style: The style of docstring.
            strictness: The minimum strictness to allow.
            ignore_regex: A regular expression which enables ignoring
                functions/methods by name.
            ignore_raise: A list of exceptions that don't need to be
                documented.
            ignore_properties: Bool indicating whether to ignore properties functions
                or not.
            enable: A list of of error codes that are disabled by default.
            indentation: The number of spaces to count as an indent.
            assert_style: The assert style to use (e.g. log on failed
                assertions, or raise exception on failed assertions.)

        """
        self._enable = enable
        self._ignore = ignore
        self.message_template = message_template
        self.style = style
        self.strictness = strictness
        self.errors_to_ignore = self._get_errors_to_ignore()
        self.ignore_regex = ignore_regex
        self.ignore_raise = ignore_raise
        self.ignore_properties = ignore_properties
        self.indentation = indentation
        self.assert_style = assert_style
        self.log_level = log_level

    @property
    def log_level(self):
        # type: () -> LogLevel
        return self._log_level

    @log_level.setter
    def log_level(self, log_level):
        # type: (LogLevel) -> None
        self._log_level = log_level
        logger = get_logger()
        logger.setLevel(log_level.value)

    def __str__(self):
        # type: () -> str
        return '\n'.join([
            'message_template={message_template}',
            'style={style}',
            'strictness={strictness}',
            'indentation={indentation}',
            'ignore={errors_to_ignore}',
            'ignore_regex={ignore_regex}',
            'ignore_raise={ignore_raise}',
        ]).format(**self.__dict__)

    @classmethod
    def get_default_instance(cls):
        return cls(
            ignore=list(),
            message_template=None,
            style=DocstringStyle.GOOGLE,
            strictness=Strictness.FULL_DESCRIPTION,
        )

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
        ImportError: When trying to load a ".toml"-file without `tomli` installed.
        Exception: When the configuration style is not a valid choice.

    Returns:
        A Configuration object.

    """
    darglint_config = None
    ignore = list()
    enable = list()
    message_template = None
    ignore_regex = None
    ignore_raise = list()
    ignore_properties = False
    style = DocstringStyle.GOOGLE
    strictness = Strictness.FULL_DESCRIPTION
    indentation = 4
    log_level = LogLevel.CRITICAL
    if filename.lower().endswith('.toml'):
        if not _has_tomli:
            raise ImportError("Missing optional dependency `tomli`. Install with `pip install darglint['toml']`.")
        with open(filename, "rb") as bin_config_file:
            config = tomli.load(bin_config_file)
            if 'darglint' in config['tool']:
                darglint_config = config['tool']['darglint']
    else:
        config = configparser.ConfigParser()
        config.read(filename)
        if 'darglint' in config.sections():
            darglint_config = config['darglint']
    if darglint_config is not None:
        if 'ignore' in darglint_config:
            errors = darglint_config['ignore']
            for error in errors.split(','):
                ignore.append(error.strip())
        if 'enable' in darglint_config:
            to_enable = darglint_config['enable']
            for error in to_enable.split(','):
                enable.append(error.strip())
        if 'message_template' in darglint_config:
            message_template = darglint_config['message_template']
        if 'ignore_regex' in darglint_config:
            ignore_regex = darglint_config['ignore_regex']
        if 'ignore_raise' in darglint_config:
            to_ignore_raise = darglint_config['ignore_raise']
            for exception in to_ignore_raise.split(','):
                ignore_raise.append(exception.strip())
        if 'ignore_properties' in darglint_config:
            ignore_properties = bool(darglint_config['ignore_properties'])
        if 'docstring_style' in darglint_config:
            raw_style = darglint_config['docstring_style']
            style = DocstringStyle.from_string(raw_style)

        if 'strictness' in darglint_config:
            raw_strictness = darglint_config['strictness']
            strictness = Strictness.from_string(raw_strictness)

        if 'indentation' in darglint_config:
            try:
                indentation = int(darglint_config['indentation'])
            except ValueError:
                raise Exception(
                    'Unrecognized value for indentation.  Expected '
                    'a non-zero, positive integer, but received {}'.format(
                        darglint_config['indentation']
                    )
                )

        if 'log_level' in darglint_config:
            log_level = LogLevel.from_string(darglint_config['log_level'])
    return Configuration(
        ignore=ignore,
        message_template=message_template,
        style=style,
        strictness=strictness,
        ignore_regex=ignore_regex,
        ignore_raise=ignore_raise,
        ignore_properties=ignore_properties,
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
    try:
        filenames = os.listdir(path)
    except PermissionError:
        return None
    for filename in filenames:
        if filename in POSSIBLE_CONFIG_FILENAMES:
            fully_qualified_path = os.path.join(path, filename)
            if filename.lower().endswith('.toml'):
                try:
                    with open(filename, "rb") as bin_config_file:
                        config = tomli.load(bin_config_file)
                    if 'darglint' in config['tool']:
                        return fully_qualified_path
                except tomli.TOMLDecodeError:
                    get_logger().error('Unable to parse file {}'.format(
                        fully_qualified_path
                    ))
            else:
                config = configparser.ConfigParser()
                try:
                    config.read(fully_qualified_path)
                    if 'darglint' in config.sections():
                        return fully_qualified_path
                except configparser.ParsingError:
                    get_logger().error('Unable to parse file {}'.format(
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


def get_config_from_file():  # type: () -> Configuration
    """Locate the configuration file and return its Configuration.

    Returns:
        The Configuration described in the nearest configuration file,
        otherwise an empty Configuration.

    """
    filename = find_config_file()
    if filename is None:
        return Configuration.get_default_instance()
    return load_config_file(filename)


# The global instance of the config file to use.
_config = get_config_from_file()


def get_config():
    """Get the global instance of the configuration.

    This instance is not threadsafe, and should only
    be updated in the initial launching script.
    I considered adding a mutability option, to make
    this more explicit, but I think it's obvious enough
    that you shouldn't modify the configuration elsewhere.

    Returns:
        A global configuration instance.

    """
    return _config
