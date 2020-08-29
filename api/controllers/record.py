# Third-party Imports
import falcon
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Local Imports
from config import Config
from models import Record
from utils.validator import RecordValidator, InvalidDNSRecord, InvalidDNSRecordType


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
        if not all(map(req.media.get, ('resource', 'rdata'))):
            raise falcon.HTTPBadRequest('Missing Body Parameters',
                                        'Missing \'resource\', \'rdata\' or \'ttl\' in the request body.')

        # Retrieve mandatory body parameters
        rdata = req.media.get('rdata')
        resource = req.media.get('resource')

        # Retrieve optional body parameters
        ttl = req.media.get('ttl', Config.get('default-record-ttl', 3600))

        # Validate Record
        try:
            RecordValidator.validate(zone, resource, rtype, rdata)
        except (InvalidDNSRecord, InvalidDNSRecordType) as e:
            raise falcon.HTTPConflict('Conflict', str(e))

        # Create and add record entity to transaction
        record = Record(zone=zone, resource=resource, rtype=rtype, ttl=ttl, rdata=rdata)
        self.dbconn.add(record)

        # Attempt database changes commit
        try:
            self.dbconn.commit()

        except IntegrityError as e:

            # Rollback transaction
            self.dbconn.rollback()

            # Raise 409 conflict
            raise falcon.HTTPConflict('Conflict', 'Record already exists.')

        except SQLAlchemyError as e:

            # Rollback transaction
            self.dbconn.rollback()

            # Raise 500 internal server error
            raise falcon.HTTPInternalServerError('Internal Server Error', f'Message: {str(e)}')

        resp.media, resp.status_code = {
            'zone': record.zone,
            'resource': record.resource,
            'rtype': record.rtype,
            'ttl': record.ttl,
            'rdata': record.rdata
        }, falcon.HTTP_201
