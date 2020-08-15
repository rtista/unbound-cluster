# Batteries
import os
import sys
import signal
import multiprocessing

# Third-party Imports
import setproctitle
from loguru import logger

# Local Imports
from .logger import StreamToLogger


class UnixProcess(multiprocessing.Process):
    """
    An Unix Process is capable of handling kill signals
    with the associated handler functions and set its proctitle.
    """

    def __init__(self, name):
        """
        Create a new Unix Process class instance.
        Args:
            name (str): The process name.
        """
        multiprocessing.Process.__init__(self, name=name)
        self._stop = False

    def setprocname(self):
        """
        Sets the process name/title to the process name.
        Should be called in the process 'run' method.
        """
        setproctitle.setproctitle(f'unbound-cluster: {self.name}')

    def sighandler(self, signum, frame):
        """
        Sets _stop to True so the consumer stops
        consuming and terminates itself.
        Args:

            signum (int): The signal received.
            frame (frame): The process which killed this one.
        """
        logger.info(f'Received signal {signum}. Shutting down.')
        self._stop = True

    @staticmethod
    def sigreg(signum, function):
        """
        Allows registering signal handlers.

        Args:
            signum (int): The signal number.
            function (function): The function to execute.
        """
        signal.signal(signum, function)

    @staticmethod
    def daemonize():
        """
        Detaches the process from the lauching session.
        """
        # Fork allows background running
        if os.fork():
            exit(0)

        # Clear the session id to clear the controlling TTY.
        os.setsid()

        # Set the umask so we have access to all files created by the daemon.
        os.umask(0)

        # Shutdown stdin
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())

        # Remove Default handlers
        logger.remove(None)

        # Add handling for stdout and stderr
        sys.stdout = StreamToLogger('INFO')
        sys.stderr = StreamToLogger('ERROR')
