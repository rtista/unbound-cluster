# Batteries
import os
import time
import json
import signal
import threading
import contextlib

# Third-party imports
import requests
from loguru import logger

# Local Imports
from config import Config


class ClusterSlave(threading.Thread):
    """
    A client which syncs changes into the local unbound instance.

    Args:
        threading.Thread (class): The Thread class.
    """

    def __init__(self):
        """
        Create an instance of the unbound cluster sync client.
        """
        super().__init__(name='cluster-slave')
        self._localdata_dir = Config.getpath('cluster-slave.local-data-dir')
        self._unbound_pidfile = Config.getpath('cluster-slave.unbound-pid')
        self._master_location = Config.get('cluster-slave.master-location')
        self._stop = False
        self._lastupdate = 0

    def _unboundreload(self):
        """
        Reloads unbound configurations by sending a SIGHUP signal to the process.

        Returns:
            bool: Success of the operation.
        """
        # If pid file does not exist log and return
        if not os.path.isfile(self._unbound_pidfile):
            logger.warning(f'Could not find unbound pidfile at {self._unbound_pidfile}... Not reloading...')
            return False

        # Read unbound process pid from pid file
        with open(self._unbound_pidfile, 'r') as pidfile:

            # Read pidfile
            pid = int(pidfile.readline())

            # If pid does not exist, log and return
            if not os.path.isdir(f'/proc/{pid}'):
                logger.warning(f'Stale pidfile at {self._unbound_pidfile}... Not reloading...')
                return False

            logger.info(f'Reloading unbound instance with pid {pid}...')

            # Send SIGHUP to process
            os.kill(pid, signal.SIGHUP)

        return True

    def stopthread(self):
        """
        Stops the thread execution.
        """
        self._stop = True

    @logger.catch
    def run(self):
        """
        This will run in a separate thread.
        """
        while not self._stop:

            # Query API for most recently updates
            try:

                # Retrieve most recent
                resp = requests.get(f'{self._master_location}/zone?updated={self._lastupdate}')

                # Continue on API error
                if resp.status_code != 200:
                    logger.warning(f'API responded with {resp.status_code} HTTP status code.')
                    raise

                # For each updated zone
                for zone in resp.json().get('zones'):

                    # Request updated records from zone
                    records = requests.get(f'{self._master_location}/zone/{zone}/record')

                    # No new records
                    if not records.json().get('records'):
                        break

                    # Check if zones directory exists
                    if not os.path.isdir(self._localdata_dir):
                        os.makedirs(self._localdata_dir)

                    # Flush changes to file
                    with open(f'{self._localdata_dir}/{zone}.conf', 'w+') as zonefile:
                        zonefile.write(f'server:\n\nlocal-zone: "e-goi.com" transparent\n\n')
                        zonefile.writelines([ f'local-data: "{" ".join((".".join((r["resource"], r["zone"])), r["rtype"], str(r["ttl"]), r["rdata"]))}"\n' for r in records.json().get("records") ])

                # If there were any modified zones
                if resp.json().get('zones'):
                    logger.info(f'Received update from zones: {str(resp.json().get("zones"))}...')
                    self._unboundreload()

                # Update lastupdate variable
                self._lastupdate = int(time.time())

            except Exception as e:
                logger.error(f'Caught unexpected {str(e.__class__.__name__)} exception: {str(e)}')

            # Rest for a while
            time.sleep(5)
