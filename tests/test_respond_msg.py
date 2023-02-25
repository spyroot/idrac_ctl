import logging
import os
from unittest import TestCase

from idrac_ctl.idrac_manager import IDracManager
from idrac_ctl.redfish_manager import RedfishManager
from requests.models import Response
from unittest.mock import Mock
from requests.models import Response

the_response = Mock(spec=Response)

logging.basicConfig()
log = logging.getLogger("LOG")


class TestRedfishRespondMsg(TestCase):
    redfish_api = None

    def test_base_respond(self):
        data = {
            '@Message.ExtendedInfo':
                [
                    {
                        'Message': 'The request completed successfully.',
                        'MessageArgs': [], 'MessageArgs@odata.count': 0,
                        'MessageId': 'Base.1.12.Success',
                        'RelatedProperties': [],
                        'RelatedProperties@odata.count': 0,
                        'Resolution': 'None',
                        'Severity': 'OK'
                    }
                ],
            'DriversAttachStatus': 'NotAttached',
            'ISOAttachStatus': 'NotAttached'
        }

        resp = Mock(spec=Response)
        resp._content = data
        resp.status_code = 200
        redfish_resp = RedfishManager.parse_json_respond_msg(resp)
        self.assertTrue(
            redfish_resp.status_code == 200,
            f"status code must be 200"
        )
        log.warning("Redfish status code", redfish_resp.status_code)

    def test_base_respond_with_pd(self):
        data = {
            '@Message.ExtendedInfo':
                [
                    {
                        'Message': 'The request completed successfully.',
                        'MessageArgs': [], 'MessageArgs@odata.count': 0,
                        'MessageId': 'Base.1.12.Success',
                        'RelatedProperties': [],
                        'RelatedProperties@odata.count': 0,
                        'Resolution': 'None',
                        'Severity': 'OK'
                    }
                ],
            'DriversAttachStatus': 'NotAttached',
            'ISOAttachStatus': 'NotAttached'
        }

        resp = Mock(spec=Response)
        resp._content = data
        resp.status_code = 200
        redfish_resp = RedfishManager.parse_json_respond_msg(resp)
        self.assertTrue(
            redfish_resp.status_code == 200,
            f"status code must be 200"
        )
        log.warning("Redfish status code", redfish_resp.status_code)

