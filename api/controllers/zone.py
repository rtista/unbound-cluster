# Third-party Imports
import falcon
import sqlalchemy

# Local Imports
from models import Record


class ZoneController:
    """
    Represents the Zone controller which handles zone CRUD requests.
    """

    def on_get(self, req, resp):
        """
        Handles GET requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        """
        # Select all zones from the database
        queryset = self.dbconn.query(sqlalchemy.distinct(Record.zone)).all()

        resp.media = { 'zones': [ zone for (zone, ) in queryset ] }
        resp.status = falcon.HTTP_200
