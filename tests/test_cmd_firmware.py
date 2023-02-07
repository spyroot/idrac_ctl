import json
import os
from unittest import TestCase

from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.shared import ApiRequestType
import urllib3
urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Test(TestCase):
    redfish_api = None

    @classmethod
    def setUpClass(cls) -> IDracManager:
        redfish_api = IDracManager(idrac_ip=os.environ.get('IDRAC_IP', ''),
                                   idrac_username=os.environ.get('IDRAC_USERNAME', 'root'),
                                   idrac_password=os.environ.get('IDRAC_PASSWORD', ''),
                                   insecure=True,
                                   is_debug=False)
        return redfish_api

    def setUp(self) -> None:
        self.assertTrue(len(os.environ.get('IDRAC_IP', '')) > 0, "IDRAC_IP is none")
        self.assertTrue(len(os.environ.get('IDRAC_USERNAME', '')) > 0, "IDRAC_USERNAME is none")
        self.assertTrue(len(os.environ.get('IDRAC_PASSWORD', '')) > 0, "IDRAC_PASSWORD is none")

    def test_firmware_query(self):
        manager = self.setUpClass()
        result = manager.sync_invoke(
            ApiRequestType.FirmwareQuery, "firmware_query")
        self.assertIsInstance(result, CommandResult)
        self.assertIsInstance(result.data, dict)
        try:
            json.dumps(result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")
        self.assertTrue('Members' in result.data, "Failed to fetch mandatory key")

    def test_firmware_deep_query(self):
        manager = self.setUpClass()
        result = manager.sync_invoke(
            ApiRequestType.FirmwareQuery, "firmware_query", do_deep=True)
        self.assertIsInstance(result, CommandResult)
        self.assertIsInstance(result.data, dict)
        try:
            json.dumps(result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        self.assertTrue('Members' in result.data, "Failed to fetch mandatory key")