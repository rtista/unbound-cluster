#!/usr/bin/python3

# Batteries
import os
import signal
import time
from argparse import ArgumentParser

# Own Imports
from config import Config, InvalidConfiguration
from master import UnboundClusterMaster


def stop():
    """
    Stops the master process.
    """
    # Check for pidfile
    if not os.path.isfile(Config.getpath('pidfile')):
        print('Could not find pidfile. Is the process running?')
        return

    # Read Supervisor PID from pidfile
    with open(Config.getpath('pidfile'), 'r') as pidfile:
        pid = int(pidfile.readline())

    # Check for running pid
    if not os.path.isdir(f'/proc/{pid}'):

        # Remove pidfile
        os.unlink(Config.getpath('pidfile'))

        # Also remove socket file if existent
        if os.path.isfile(Config.getpath('socket')):
            os.unlink(Config.getpath('socket'))

        print('Process is not running. Removed stale pidfile and socket.')

        return

    # Send SIGTERM to process
    os.kill(pid, signal.SIGINT)

    # Wait for process to end
    while os.path.isdir(f'/proc/{pid}'):
        print('Waiting for Unbound Cluster to stop...')
        time.sleep(1)


def start():
    """
    Starts the master process.
    """
    # Check for pidfile existence
    if os.path.isfile(Config.getpath('pidfile')):

        # Check for stale PID file
        with open(Config.getpath('pidfile'), 'r') as pidfile:

            pid = pidfile.read()

            # Check if process with PID is running
            if os.path.isdir(f'/proc/{pid}'):
                print(f'Unable to start. Process already running with pid {pid}.')
                exit(0)

        # Remove stale PID file
        print(f'Found stale pid file at {Config.get("pidfile")}. Removing...')
        os.unlink(Config.getpath('pidfile'))

        # Remove stale socket if existent
        if os.path.isfile(Config.getpath('socket')):
            os.unlink(Config.getpath('socket'))

    # Create and start the master process
    UnboundClusterMaster().start()


def restart():
    """
    Restarts the master process.
    """
    stop()
    start()


# Available operations
OPERATIONS = {
    'stop': stop,
    'start': start,
    'restart': restart
}

# Main
if __name__ == '__main__':

    # Create argument parser
    parser = ArgumentParser(description='Unbound Cluster Controller')
    parser.add_argument('operation', type=str, choices=OPERATIONS.keys(),
                        help=f'The operation to execute. Possible values: {", ".join(OPERATIONS.keys())}')

    # Parse Arguments
    args = parser.parse_args()

    # Execute requested operation
    try:
        # Execute Operation
        OPERATIONS[args.operation]()

    except InvalidConfiguration as e:

        print(f'Invalid Configuration: {str(e)}')
        exit(1)

    except Exception as e:
        print(f'Unknown error occurred: {str(e)}')
        exit(1)
