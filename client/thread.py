# Batteries
import os
import time
import json
import threading
import contextlib

# Third-party imports
import requests
from loguru import logger

# Local Imports
from config import Config


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
        super().__init__(name='unbound-cluster-syncer')
        self._stop = False
        self._lastupdate = 0

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
                resp = requests.get(f'{Config.get("unbound-cluster-api")}/zone?updated={self._lastupdate}')

                # Continue on API error
                if resp.status_code != 200:
                    logger.warning(f'API responded with {resp.status_code} HTTP status code.')
                    raise

                # For each updated zone
                for zone in resp.json().get('zones'):

                    # Request updated records from zone
                    records = requests.get(f'{Config.get("unbound-cluster-api")}/zone/{zone}/record')

                    # No new records
                    if not records.json().get('records'):
                        break

                    # TODO: Update local-data configuration files
                    logger.info(f'Updating {len(records.json())} zones. Resp: {json.dumps(records.json())}')

                    # Check if zones directory exists
                    if not os.path.isdir(Config.getpath('unbound-zones-dir')):
                        os.makedirs(Config.getpath('unbound-zones-dir'))

                    # Flush changes to file
                    with open(f'{Config.getpath("unbound-zones-dir")}/{zone}.conf', 'w+') as zonefile:
                        zonefile.write(f'server:\n\nlocal-zone: "e-goi.com" transparent\n\n')
                        zonefile.writelines([ f'local-data: "{" ".join((".".join((r["resource"], r["zone"])), r["rtype"], str(r["ttl"]), r["rdata"]))}"\n' for r in records.json().get("records") ])
                        zonefile.write('\n')

                # Update lastupdate variable
                self._lastupdate = int(time.time())

            except Exception as e:
                logger.error(f'Caught unexpected {str(e.__class__.__name__)} exception: {str(e)}')

            # Rest for a while
            time.sleep(5)
