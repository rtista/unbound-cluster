# Batteries
import contextlib
import os
import signal
import time
from datetime import timedelta

# Third-party
from loguru import logger

# Local Imports
from config import Config
from utils.process import UnixProcess


class UnboundClusterMaster(UnixProcess):
    """
    The unbound cluster master process will monitor the required interfaces.

    Args:
        shared.process.UnixProcess (class): UnixProcess class.
    """

    def __init__(self):
        """
        Creates the process.
        """
        super().__init__('master process')

    def _monit(self):
        """
        Monitors the instances of required threads.
        """
        return

    @logger.catch
    def run(self):
        """
        This will run in a separate process.
        """
        # Daemonize
        self.daemonize()

        # Create helper sink
        logger.add(
            Config.getpath('log.file'),
            level=Config.get('log.level'), colorize=True, enqueue=True,
            format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> |'
                   '<yellow>{process.name: <23}</yellow> | '
                   '<level>{message}</level> (<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>)',
            rotation=timedelta(days=1), retention=timedelta(days=30), compression='gz')

        # Set process title
        self.setprocname()

        # Set signal handlers
        self.sigreg(signal.SIGINT, self.sighandler)
        self.sigreg(signal.SIGTERM, self.sighandler)

        # Write PID file
        with open(Config.getpath('pidfile'), 'w+') as pidfile:
            pidfile.write(str(os.getpid()))

        # While not stopping
        while self._stop is False:
            # TODO: Recheck configuration file

            # Monit instances
            self._monit()

            time.sleep(1)

        logger.debug('Terminating...')

        # Remove pidfile and socket
        with contextlib.suppress(FileNotFoundError):
            os.unlink(Config.getpath('pidfile'))
