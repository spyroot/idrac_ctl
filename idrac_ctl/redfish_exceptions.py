
from functools import cached_property

class RedfishException(Exception):
    """ This base class for redfish error so we can differentiate
    critical from none critical and map to respected HTTP status code.
    """
    def __init__(self, *args, **kwargs):
        super(RedfishException, self).__init__(args, kwargs)
        self.redfish_error = kwargs.get('redfish_error')


class RedfishNotFound(RedfishException):
    """Request specified a URI of a resource that does not exist.
    """
    pass


class RedfisForbiden(RedfishException):
    """HTTTP Status code 403
    """

class RedfisMethodNotAllowed(RedfishException):
    """HTTP Status code 405 Request specified a URI of a resource that does not exist.
    """
    pass

class RedfishNotAcceptable(RedfishException):
    """HTTP status 406 header was specified in the request and the resource identified by
    this request cannot generate a representation that corresponds
    to one of the media types in the Accept header.
    """
    pass

class RedfishConflict(RedfishException):
    """HTTP status code 409
    """
    pass

class RedfishGone(RedfishException):
    """HTTP status code 410
    """
    pass