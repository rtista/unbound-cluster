# Third-party Imports
import falcon
import sqlalchemy
from loguru import logger
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
        if not zone:
            raise falcon.HTTPBadRequest('Missing URL Parameters', 'Missing \'zone\' in the request URL.')

        # Get all records of zone
        where = f'zone = "{zone}"'

        # Check if record is specified
        if rtype:
            where += f' AND type = "{rtype}"'

        # Check for updated parameter
        if 'updated' in req.params and str(req.params['updated']).isnumeric() and int(req.params['updated']) > 0:
            where += f' AND updated > {int(req.params["updated"])}'

        # For each record in the warehouse
        records = []
        for record in self.dbconn.query(Record).filter(sqlalchemy.text(where)).all():

            records.append({
                'zone': record.zone,
                'resource': record.resource,
                'rtype': record.rtype,
                'ttl': record.ttl,
                'rdata': record.rdata,
                'created': record.created,
                'updated': record.updated,
            })

        resp.media = { 'records': records }
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
