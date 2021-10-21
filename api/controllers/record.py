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
    def on_get(self, req: falcon.Request, resp: falcon.Response, rtype: str = None, rname: str = None):
        """
        Handles GET requests.
        """
        where = []

        # Check if record type is specified
        if rtype:
            where.append(f'rtype = "{rtype}"')

        # Check if record name is specified
        if rname:
            where.append(f'rname = "{rname}"')

        # Check for updated parameter
        if 'updated' in req.params and str(req.params['updated']).isnumeric() and int(req.params['updated']) > 0:
            where.append(f'updated > {int(req.params["updated"])}')

        # For each record retrieved from database
        records = [r.todict() for r in
                   req.context.dbconn.query(Record).filter(sqlalchemy.text(' AND '.join(where))).all()]

        resp.status, resp.media = falcon.HTTP_200, {'records': records}

    def on_post(self, req: falcon.Request, resp: falcon.Response, rtype: str = None):
        """
        Handles POST requests.
        """
        # Check URL parameters
        if not rtype:
            raise falcon.HTTPBadRequest(
                title='Missing URL Parameters', description='Resource type identifier is required in the URL.')

        try:
            # Retrieve body parameters
            rname, rdata, ttl = req.media['rname'], req.media['rdata'], \
                                req.media.get('ttl', Config.get('default-record-ttl', 3600))

            # Validate record
            RecordValidator.validate(rname, rtype, rdata)

            # Create record entity
            record = Record(rname=rname, rtype=rtype, ttl=ttl, rdata=rdata)

            # Add and commit database transaction
            req.context.dbconn.add(record)
            req.context.dbconn.commit()

        except KeyError as e:
            raise falcon.HTTPBadRequest(
                title='Missing Body Parameters', description=f'Missing \'{str(e)}\' in the request body.')

        except (InvalidDNSRecord, InvalidDNSRecordType) as e:
            raise falcon.HTTPConflict(title='Conflict', description=str(e))

        except IntegrityError:

            # Rollback transaction
            req.context.dbconn.rollback()

            # Raise 409 conflict
            raise falcon.HTTPConflict(title='Conflict', description='Record already exists.')

        except SQLAlchemyError as e:

            # Rollback transaction
            req.context.dbconn.rollback()

            # Raise 500 internal server error
            raise falcon.HTTPInternalServerError(title='Internal Server Error', description=f'Message: {str(e)}')

        resp.status_code, resp.media = falcon.HTTP_201, {
            'rname': record.rname,
            'rtype': record.rtype,
            'rdata': record.rdata,
            'ttl': record.ttl,
        }

    def on_put(self, req: falcon.Request, resp: falcon.Response, rtype: str = None, rname: str = None):
        """
        Handles PUT requests.
        """
        # Check URL parameters
        if not rtype:
            raise falcon.HTTPBadRequest(
                title='Missing URL Parameters', description='Resource type identifier is required in the URL.')

        if not rname:
            raise falcon.HTTPBadRequest(
                title='Missing URL Parameters', description='Resource name identifier is required in the URL.')

        # Save update statement where parameters
        where = {'rtype': rtype, 'rname': rname}

        try:
            # Retrieve body parameters
            values = {p: req.media.get(p) for p in ('rname', 'rdata', 'ttl') if req.media.get(p)}

            # Validate record
            RecordValidator.validate(values.get('rname', rname), rtype, values['rdata'])

            # Add and commit database transaction
            updated = req.context.dbconn.query(Record).filter_by(**where).update(values, synchronize_session=False)
            req.context.dbconn.commit()

            # If no rows were updated, insert
            if updated == 0:

                # Add and commit database transaction
                req.context.dbconn.add(
                    Record(rname=values.get('rname', rname), rtype=rtype, rdata=values['rdata'], ttl=values.get('ttl')))
                req.context.dbconn.commit()

        except KeyError as e:
            raise falcon.HTTPBadRequest(
                title='Missing Body Parameters', description=f'Missing \'{str(e)}\' in the request body.')

        except (InvalidDNSRecord, InvalidDNSRecordType) as e:
            raise falcon.HTTPConflict(title='Conflict', description=str(e))

        except IntegrityError:

            # Rollback transaction
            req.context.dbconn.rollback()

            # Raise 409 conflict
            raise falcon.HTTPConflict(title='Conflict', description='Record already exists.')

        except SQLAlchemyError as e:

            # Rollback transaction
            req.context.dbconn.rollback()

            # Raise 500 internal server error
            raise falcon.HTTPInternalServerError(title='Internal Server Error', description=f'Message: {str(e)}')

        resp.status_code, resp.media = falcon.HTTP_200, {
            'rname': values.get('rname', rname),
            'rtype': rtype,
            'rdata': values.get('rdata'),
        }

    def on_delete(self, req: falcon.Request, resp: falcon.Response, rtype: str = None, rname: str = None):
        """
        Handles DELETE requests.

        Args:
            req (falcon.Request): The request object.
            resp (falcon.Response): The response object.
            rtype (str): The record type.
            rname (str): The record name.
        """
        # Check URL parameters
        if not rtype:
            raise falcon.HTTPBadRequest(
                title='Missing URL Parameters', description='Resource type identifier is required in the URL.')

        # Validate rname
        if not rname:
            raise falcon.HTTPBadRequest(
                title='Bad Request', description='Resource name identifier is required in the URL.')

        # Save update statement where parameters
        where = {'rtype': rtype, 'rname': rname}

        try:
            # Delete rname and commit
            deleted = req.context.dbconn.query(Record).filter_by(**where).delete(synchronize_session=False)
            req.context.dbconn.commit()

            # Set response code and body
            resp.status, resp.media = falcon.HTTP_204, {'deleted': deleted}

        except SQLAlchemyError as e:

            # Rollback transaction
            req.context.dbconn.rollback()

            # Raise 500 internal server error
            raise falcon.HTTPInternalServerError(title='Internal Server Error', description=f'Message: {str(e)}')
