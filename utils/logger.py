# Third-party Import
from loguru import logger


class StreamToLogger(object):
    """
    A stream which logs its input into a loguru sink.

    Args:
        builtins.object (class): Default base object class.
    """

    def __init__(self, level="INFO"):
        """
        Creates the StreamToLogger instance.

        Args:
            level (str, optional): The level of luguru logging to use. Defaults to "INFO".
        """
        self._level = level

    def write(self, buffer):
        """
        Writes buffer contents into as log messages.

        Args:
            buffer ([type]): The buffer.
        """
        for line in buffer.rstrip().splitlines():
            logger.log(self._level, line.rstrip())

    def flush(self):
        """
        Override default behavior.
        """
        pass
