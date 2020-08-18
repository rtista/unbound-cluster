# Third-party Imports
import falcon


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
        res = self.dbconn.execute('''SELECT DISTINCT zone FROM records''')

        resp.media = { 'zones': [ z for z in res ] }
        resp.status = falcon.HTTP_200
