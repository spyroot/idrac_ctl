
class RedfishException(Exception):
    """ This base class for redfish error so we can differentiate
    critical from none critical and map to respected HTTP status code.
    """
    def __init__(self, *args, **kwargs):
        super(RedfishException, self).__init__(args, kwargs)
        self.redfish_error = kwargs.get('json_error')


class RedfishException(Exception):
    def __init__(self, *args, **kwargs):
        super(RedfishException, self).__init__(args, kwargs)
        self.redfish_error = kwargs.get('json_error')

