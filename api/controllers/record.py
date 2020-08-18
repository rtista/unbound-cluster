# Third-party Imports
import falcon


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

        resp.media = req.media
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, zone=None, rtype=None):
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

        # Check body parameters
        if not all(map(req.media.get, ('resource', 'rdata', 'ttl'))):
            raise falcon.HTTPBadRequest('Missing Body Parameters', 'Missing \'resource\', \'rdata\' or \'ttl\' in the request body.')

        account = Account(name=account_name)

        self.db_conn.add(account)

        # Attempt database changes commit
        try:
            # Create Account
            self.db_conn.commit()

            # Now create main user for account
            user = User(account_id=account.account_id, username=username, password=hashed)

            self.db_conn.add(user)

            self.db_conn.commit()

        except SQLAlchemyError as e:

            # Remove Changes
            self.db_conn.rollback()

            # Send error
            resp.media = {'error': 'Message: {}'.format(str(e))}
            resp.status_code = falcon.HTTP_500
            return

        resp.media = {'success': 'Account created successfuly'}
        resp.status_code = falcon.HTTP_201

        resp.media = req.media
        resp.status = falcon.HTTP_201
