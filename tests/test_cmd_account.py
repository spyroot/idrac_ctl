import json
import os
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.idrac_shared import ApiRequestType
import logging

logging.basicConfig()
log = logging.getLogger("LOG")


class TestAccounts(TestCase):
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

    def test_basic_account_query(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.QueryAccount, "query_account", account=1)

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, dict)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        self.assertTrue("AccountTypes" in query_result.data,
                        f"Failed to fetch mandatory AccountTypes key")
