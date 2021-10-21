# Local imports
from .record import RecordController

# The base point for each route
BASE_ENDPOINT = '/api'

# Declare all your routes here
ROUTES = {

    # Zone Controller
    '/record': RecordController,
    '/record/{rtype}': RecordController,
    '/record/{rtype}/{rname}': RecordController
}
