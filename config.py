# Batteries
import json
import os
from functools import reduce

# Third-party Imports
from loguru import logger


class InvalidConfiguration(Exception):
    """
    Thrown when the read configuration is missing
    mandatory parameters or is an invalid JSON format.

    Args:
        builtins.Exception (class): Builtin exception class.
    """
    ...


class Config(object):
    """
    Base configuration class. Reads data from config.json file
    and allows retrieving that data.

    Configurations are cached in memory for faster access.

    Args:
        builtins.object (class): Builtin object class.
    """
    # Base directory
    BASE_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)))

    # Default configuration file
    CONFIG_FILE_PATH = f'{BASE_DIR}/config.json'

    # Supported record types
    SUPPORTED_RECORD_TYPES = ('A', 'AAAA', 'CNAME', 'MX')

    # Class parameters
    _configfile = None
    _configdict = None

    # TODO: Validate configurations with JSON Schema package
    @classmethod
    def load(cls, path):
        """
        Loads the configuration file into memory.

        Args:
            path (str): The path for the configuration file.
        """
        try:
            # Set configuration file
            cls._configfile = path

            # Open file and read configuration into memory
            with open(cls._configfile, 'r') as configfile:
                cls._configdict = json.load(configfile)

        except FileNotFoundError:
            raise InvalidConfiguration(f'Configuration file {path} does not exist.')

        except json.JSONDecodeError:
            raise InvalidConfiguration('Configuration file contains invalid JSON format.')

    @classmethod
    def reload(cls):
        """
        Reloads the configuration file into memory.
        """
        try:
            cls.load(cls.CONFIG_FILE_PATH)
        except InvalidConfiguration as e:
            logger.error(f'Invalid configurations, not reloading. Error: {str(e)}')
            return False

        return True

    @classmethod
    def get(cls, key, default=None):
        """
        Retrieves the value for a key from the configuration file.

        Args:
            key (str): The key from which to get the value. These
                can be several splitted by a dot.
            default (object): What to return if the key is not found.

        Returns:
            object: The configuration value.
        """
        # Retrieve configurations if not loaded
        if not cls._configdict:
            cls.load(cls.CONFIG_FILE_PATH)

        value = reduce(dict.get, key.split('.'), cls._configdict)

        return default if value is None else value

    @classmethod
    def getpath(cls, key):
        """
        Utility function to retrieve a key whose value is a
        filesystem path. This will read both absolute and
        relative paths and always return an absolute path.

        If relative, the path will be prefixed with the
        project's root.

        Args:
            key (str): The key from which to get the value. These
                can be several splitted by a dot.

        Returns:
            str: The absolute path.
        """
        # Read path from configuration
        path = str(cls.get(key))

        # Prevent empty value
        if not path:
            return None

        # Return path or absolute path from base dir
        return path if os.path.isabs(path) else f'{cls.BASE_DIR}/{path}'
