# Local imports
from .zone import ZoneController
from .record import RecordController

# The base point for each route
BASE_ENDPOINT = '/api'

# Declare all your routes here
ROUTES = {

    # Zone Controller
    '/zone': ZoneController,
    '/zone/{zone}': ZoneController,
    '/zone/{zone}/{rrtype}/': RecordController
}
