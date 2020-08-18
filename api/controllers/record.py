# Third-party Imports
import falcon

# Third-party Imports
from sqlalchemy.exc import SQLAlchemyError, NoReferenceError

# Local Imports
from models import Record


class RecordController(object):
    """
    Represents the Record controller which handles Record CRUD requests.
    """

    def on_get(self, req, resp, zone=None, rtype=None):
        """
        Handles GET requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        :param rtype: The record type.
        """
        # Check URL parameters
        if None in (zone, rtype):
            raise falcon.HTTPBadRequest('Missing URL Parameters', 'Missing \'zone\' or \'rtype\' in the request URL.')

        # Get all records of zone
        query = self.dbconn.query(Record).filter(Record.zone == zone)

        # Check if record is specified
        if rtype:
            query.filter(Record.rtype == rtype)

        resp.media = { 'records': [ r.resource for r in query.all() ] }
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, zone=None, rtype=None):
        """
        Handles POST requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        :param rtype: The record type.
        """
        # Check URL parameters
        if None in (zone, rtype):
            raise falcon.HTTPBadRequest('Missing URL Parameters', 'Missing \'zone\' or \'rtype\' in the request URL.')

        # Check body parameters
        if not all(map(req.media.get, ('resource', 'rdata', 'ttl'))):
            raise falcon.HTTPBadRequest('Missing Body Parameters', 'Missing \'resource\', \'rdata\' or \'ttl\' in the request body.')

        # Retrieve body parameters
        resource = req.media.get('resource')
        ttl = req.media.get('ttl')
        rdata = req.media.get('rdata')

        # Create and add record entity to transaction
        record = Record(zone=zone, resource=resource, rtype=rtype, ttl=ttl, rdata=rdata)
        self.dbconn.add(record)

        # Attempt database changes commit
        try:
            self.dbconn.commit()
        except SQLAlchemyError as e:

            # Rollback transaction and raise error
            self.dbconn.rollback()
            raise falcon.InternalServerError('Internal Server Error', f'Message: {str(e)}')

        resp.media = {'zone': record.zone, 'resource': record.resource, 'rtype': record.rtype, 'ttl': record.ttl, 'rdata': record.rdata}
        resp.status_code = falcon.HTTP_201
