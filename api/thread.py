# Batteries
import threading

# Third-party imports
import bjoern
import falcon
from loguru import logger

# Local Imports
from .middleware import LoggingMiddleware
from .controllers import BASE_ENDPOINT, ROUTES


class UnboundClusterAPI(threading.Thread):
    """
    Represents the REST API interface.

    Args:
        threading.Thread (class): The Thread class.
    """

    def __init__(self, bind='127.0.0.1', port=8000):
        """
        Create an instance of the REST API interface.

        Args:
            bind (str, optional): The bind address for the API process. Defaults to '127.0.0.1'.
            port (int, optional): The port to which to bind. Defaults to 8000.
        """
        super().__init__()
        self._bind = bind
        self._port = port

    @logger.catch
    def run(self):
        """
        This will run in a separate thread.
        """
        # Create WSGI Application
        api = falcon.API(
            middleware=[
                LoggingMiddleware(),
            ]
        )

        # Route Loading
        for route in ROUTES:
            api.add_route(f'{BASE_ENDPOINT}{route}', ROUTES[route]())

        # Start WSGI server
        logger.info(f'Starting bjoern server on {self._bind}:{self._port}')

        try:
            bjoern.run(api, self._bind, self._port)
        except Exception as e:
            logger.info(f'Shutting down bjoern due to: {str(e)}')
