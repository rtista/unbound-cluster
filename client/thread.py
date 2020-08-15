# Batteries
import threading

# Third-party imports
import time
from loguru import logger


class UnboundClusterSyncer(threading.Thread):
    """
    A client which syncs changes into the local unbound instance.

    Args:
        threading.Thread (class): The Thread class.
    """

    def __init__(self):
        """
        Create an instance of the unbound cluster sync client.
        """
        super().__init__()
        self._stop = False

    @logger.catch
    def run(self):
        """
        This will run in a separate thread.
        """
        while not self._stop:

            logger.trace('Checking for changes')

            # TODO: Query API/Database

            # TODO: Update local-data configuration files

            # Rest for a while
            time.sleep(1)
