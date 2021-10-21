# Batteries
import itertools
import os
import glob
import time
import signal
import threading

# Third-party imports
import requests
import tldextract
from loguru import logger

# Local Imports
from config import Config


class ClusterSlave(threading.Thread):
    """
    A client which syncs changes into the local unbound instance.

    Args:
        threading.Thread (class): The Thread class.
    """
    # Slave headers
    _slave_headers = {'User-Agent': 'unbound-cluster-slave'}

    # Zone record entries format for unbound
    UNBOUND_DEF_FORMAT = 'local-data: "{rname} {ttl} {rtype} {rdata}"'
    UNBOUND_PTR_FORMAT = 'local-data-ptr: "{rdata} {ttl} {rname}"'

    def __init__(self):
        """
        Create an instance of the unbound cluster sync client.
        """
        super().__init__(name='cluster-slave')
        self._localdata_dir = Config.getpath('cluster-slave.local-data-dir')
        self._unbound_pidfile = Config.getpath('cluster-slave.unbound-pid')
        self._master_location = Config.get('cluster-slave.master-location')
        self._update_interval = Config.int('cluster-slave.update-interval', 5)
        self._stop = False
        self._last_update = 0

    def _flushzone(self, zone, records):
        """
        Flushes zone records to a zone file.

        :param zone: The zone to write.
        :param records: The records to flush to the zone.
        """
        # Check if zones directory exists
        if not os.path.isdir(self._localdata_dir):
            os.makedirs(self._localdata_dir)

        recordlist = []

        for record in records:

            # If A record then also append PTR record
            if record['rtype'] == 'A':
                recordlist.append(f'{self.UNBOUND_PTR_FORMAT.format(**record)}\n')

            # Append record to list
            recordlist.append(f'{self.UNBOUND_DEF_FORMAT.format(**record)}\n')

        # Flush changes to file
        with open(f'{self._localdata_dir}/{zone}.conf', 'w+') as zonefile:
            zonefile.write(f'server:\n\nlocal-zone: "{zone}" transparent\n\n')
            zonefile.writelines(recordlist)

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

    def rzone(self, record: dict) -> str:
        """
        Returns the record's zone.
        """
        return tldextract.extract(record['rname']).registered_domain

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

            # Rest for a while
            time.sleep(1)

            # Check for update every x seconds
            if time.time() - self._last_update < self._update_interval:
                continue

            # Query API for most recently updates
            try:

                # Retrieve most recent
                resp = requests.get(
                    f'{self._master_location}/record?updated={self._last_update}', headers=self._slave_headers)

                # Continue on API error
                if resp.status_code != 200:
                    logger.warning(f'API responded with {resp.status_code} HTTP status code.')
                    continue

                # Ignore when no records were updated
                if not resp.json().get('records', []):
                    logger.debug(f'No records updated.')
                    continue

                # Retrieve all records
                resp = requests.get(f'{self._master_location}/record', headers=self._slave_headers)

                # Continue on API error
                if resp.status_code != 200:
                    logger.warning(f'API responded with {resp.status_code} HTTP status code.')
                    continue

                records, zones = resp.json().get('records', []), []

                # For each updated zone
                for zone, r in itertools.groupby(sorted(records, key=self.rzone), key=self.rzone):

                    # Append zone to
                    zones.append(zone)

                    # Flush zone changes
                    self._flushzone(zone, r)

                # Flushing zone info
                logger.info(f'Flushed zones: {zones}...')

                # Remove any unnecessary zone files
                if zones:
                    zones_to_delete = [
                        f for f in glob.glob(f'{self._localdata_dir}/*.conf')
                        if os.path.basename(f).rsplit('.', 1)[0] not in zones
                    ]

                    # Delete empty zones
                    map(os.unlink, zones_to_delete)
                    logger.info(f'Deleted empty zone files: {zones_to_delete}')

                # If records were found reload unbound to update resolution
                if records:
                    self._unboundreload()

                # Update last updated time variable
                self._last_update = int(time.time())

            except Exception:
                logger.exception(f'Caught an unexpected exception')
