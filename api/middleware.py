# Batteries
import time

# Third-party Imports
import falcon
import sqlalchemy.orm
from loguru import logger


class LoggingMiddleware(object):
    """
    Log every request received by the server.
    """
    def process_request(self, req: falcon.Request, resp: falcon.Response):
        """Process the request before routing it.

        Note:
            Because Falcon routes each request based on req.path, a
            request can be effectively re-routed by setting that
            attribute to a new value from within process_request().

        Args:
            req: Request object that will eventually be
                routed to an on_* responder method.
            resp: Response object that will be routed to
                the on_* responder.
        """
        req.context.req_start_time = time.time()

    def process_response(self, req: falcon.Request, resp: falcon.Response, resource, req_succeeded: bool):
        """Post-processing of the response (after routing).

        Args:
            req: Request object.
            resp: Response object.
            resource: Resource object to which the request was
                routed. May be None if no route was found
                for the request.
            req_succeeded: True if no exceptions were raised while
                the framework processed and routed the request;
                otherwise False.
        """
        reqtime = round(float(time.time() - req.context.req_start_time), 3)

        # Log slave requests as debug
        if req.user_agent == 'unbound-cluster-slave':
            logger.debug(f'{req.access_route} {req.method} {req.uri} {resp.status} {req_succeeded} {reqtime}')
        else:
            logger.info(f'{req.access_route} {req.method} {req.uri} {resp.status} {req_succeeded} {reqtime}')


class SQLAlchemyMiddleware(object):
    """
    Appends a SQLAlchemy connection to the database.
    """
    def __init__(self, session_manager: sqlalchemy.orm.scoping.scoped_session):
        """
        Create the middleware instance.

        Args:
            session_manager (sqlalchemy.orm.scoping.scoped_session): The scoped session class.
        """
        self.Session = session_manager

    def process_resource(self, req: falcon.Request, resp:falcon.Response, resource, params: dict):
        """
        Process the request after routing.
        Args:
            req: Request object that will be passed to the
                routed responder.
            resp: Response object that will be passed to the
                responder.
            resource: Resource object to which the request was
                routed.
            params: A dict-like object representing any additional
                params derived from the route's URI template fields,
                that will be passed to the resource's responder
                method as keyword arguments.
        """
        req.context.dbconn = self.Session()

    def process_response(self, req: falcon.Request, resp: falcon.Response, resource, req_succeeded: bool):
        """
        Post-processing of the response (after routing).
        Args:
            req: Request object.
            resp: Response object.
            resource: Resource object to which the request was
                routed. May be None if no route was found
                for the request.
            req_succeeded: True if no exceptions were raised while
                the framework processed and routed the request;
                otherwise False.
        """
        if hasattr(req.context, 'dbconn'):
            if not req_succeeded:
                req.context.dbconn.rollback()
            self.Session.remove()
