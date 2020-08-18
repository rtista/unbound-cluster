# Batteries
import threading

# Third-party imports
import bjoern
import falcon
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.exc import OperationalError

# Local Imports
from config import Config
from models import Base
from .controllers import BASE_ENDPOINT, ROUTES
from .middleware import LoggingMiddleware, SQLAlchemyMiddleware


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
        # MySQL Connection Configuration
        engine = create_engine(Config.get('datastore'))
        session_factory = sessionmaker(bind=engine)
        session = scoped_session(session_factory)

        # MySQL Table Models Configuration
        try:
            Base.metadata.create_all(engine)

        except (OperationalError) as e:
            code, message = e.orig.args
            logger.error(f'Operational Error\nCode: {code}\nMessage: {message}')
            exit(1)

        # Create WSGI Application
        api = falcon.API(
            middleware=[
                LoggingMiddleware(),
                SQLAlchemyMiddleware(session)
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
