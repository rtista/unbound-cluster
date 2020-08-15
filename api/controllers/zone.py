# Third-party Imports
import falcon


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
        resp.media = req.media
        resp.status = falcon.HTTP_200
