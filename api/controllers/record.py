# Third-party Imports
import falcon


class RecordController(object):
    """
    Represents the Record controller which handles Record CRUD requests.
    """

    def on_get(self, req, resp, zone=None, rrtype=None):
        """
        Handles GET requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        :param rrtype: The record rrtype.
        """
        resp.media = req.media
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, zone=None, rrtype=None):
        """
        Handles GET requests.

        :param req: The request object.
        :param resp: The response object.
        :param zone: The DNS zone.
        :param rrtype: The record rrtype.
        """
        resp.media = req.media
        resp.status = falcon.HTTP_201
