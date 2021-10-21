# Batteries
import contextlib
import threading

# Third-party imports
import bjoern
import falcon
from loguru import logger
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.exc

# Local Imports
from models import Base
from .controllers import BASE_ENDPOINT, ROUTES
from .middleware import LoggingMiddleware, SQLAlchemyMiddleware


def default_exception_handler(req: falcon.Request, resp: falcon.Response, ex: Exception, params: dict):
    """
    Default handler for any exception, catches the exception and logs it with loguru.
    """
    logger.exception('Caught an unexpected exception', exception=ex)

    raise falcon.HTTPInternalServerError(
        title='Internal Server Error', description='An error occurred while processing your request.')


class ClusterMaster(threading.Thread):
    """
    Represents the REST API interface.

    Args:
        threading.Thread (class): The Thread class.
    """

    def __init__(self, datastore='sqlite:///unbound-cluster.sqlite', bind='127.0.0.1', port=8000):
        """
        Create an instance of the REST API interface.

        Args:
            bind (str, optional): The bind address for the API process. Defaults to '127.0.0.1'.
            port (int, optional): The port to which to bind. Defaults to 8000.
        """
        super().__init__(name='cluster-master')
        self._datastore = datastore
        self._bind = bind
        self._port = port

    @logger.catch
    def run(self):
        """
        This will run in a separate thread.
        """
        # MySQL Connection Configuration
        engine = sqlalchemy.create_engine(self._datastore)
        session_factory = sqlalchemy.orm.sessionmaker(bind=engine)
        session = sqlalchemy.orm.scoped_session(session_factory)

        # MySQL Table Models Configuration
        try:
            Base.metadata.create_all(engine)

        except sqlalchemy.exc.OperationalError as e:
            code, message = e.orig.args
            logger.error(f'Operational Error\nCode: {code}\nMessage: {message}')
            exit(1)

        # Create WSGI Application
        api = falcon.App(
            middleware=[
                LoggingMiddleware(),
                SQLAlchemyMiddleware(session)
            ]
        )

        # Strip URL trailing slashes
        api.req_options.strip_url_path_trailing_slash = True

        # Add exception handlers
        api.add_error_handler(Exception, default_exception_handler)

        # Route Loading
        for route in ROUTES:
            api.add_route(f'{BASE_ENDPOINT}{route}', ROUTES[route]())

        # Start WSGI server
        logger.info(f'Starting bjoern server on {self._bind}:{self._port}')

        try:
            bjoern.run(api, self._bind, self._port)
        except Exception as e:
            logger.info(f'Shutting down bjoern due to: {str(e)}')

        # Dispose engine before thread shutdown
        with contextlib.suppress(sqlalchemy.exc.DatabaseError):
            engine.dispose()
