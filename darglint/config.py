"""This module reads the configuration file."""

from collections import namedtuple
import configparser
import os

POSSIBLE_CONFIG_FILENAMES = (
    '.darglint',
    'setup.cfg',
    'tox.ini',
)

# ignore: List[str] -- A list of error codes to ignore.
Configuration = namedtuple('Configuration', 'ignore')


def load_config_file(filename) -> Configuration:
    """Load the config file located at the filename.

    Args:
        filename: A valid filename to read from.

    Returns:
        A Configuration object.

    """
    config = configparser.ConfigParser()
    config.read(filename)
    ignore = list()
    if 'darglint' in config.sections():
        if 'ignore' in config['darglint']:
            errors = config['darglint']['ignore']
            for error in errors.split(','):
                ignore.append(error.strip())
    return Configuration(ignore=ignore)


def find_config_file() -> str:
    """Return the location of the config file.

    Returns:
        The location of the config file, if it exists.
        Otherwise, returns None.

    """
    # Check the current directory
    cwd_files = os.listdir()
    for possible_filename in POSSIBLE_CONFIG_FILENAMES:
        if possible_filename in cwd_files:
            return possible_filename
    return None


def get_config() -> Configuration:
    """Locate the configuration file and return its Configuration.

    Returns:
        The Configuration described in the nearest configuration file,
        otherwise an empty Configuration.

    """
    filename = find_config_file()
    if filename is None:
        return Configuration(ignore=list())
    return load_config_file(filename)
