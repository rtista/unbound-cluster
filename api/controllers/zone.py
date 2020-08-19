# Third-party Imports
import falcon
import sqlalchemy

# Local Imports
from models import Record


class ZoneController:
    """
    Represents the Zone controller which handles zone CRUD requests.
    """

    def on_get(self, req, resp, zone=None):
        """
        Handles GET requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        """
        # Get all records of zone
        where = []

        if zone:
            where.append(f'zone = "{zone}"')

        # Check for updated parameter
        if 'updated' in req.params and str(req.params['updated']).isnumeric() and int(req.params['updated']) > 0:
            where.append(f'updated > {int(req.params["updated"])}')

        # Select all zones from the database
        queryset = self.dbconn.query(Record.zone).filter(sqlalchemy.text(' AND '.join(where))).distinct().all() if where else self.dbconn.query(Record.zone).distinct().all()

        resp.media = { 'zones': [ zone for (zone, ) in queryset ] }
        resp.status = falcon.HTTP_200
