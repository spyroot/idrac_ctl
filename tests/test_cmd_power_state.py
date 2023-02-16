import json
import os
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_shared import RedfishJson


class TestPowerState(TestCase):
    """
    Test chassis power state change.
    """
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

    def test_basic_power_on_reset_type_on(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        cmd_result = manager.sync_invoke(
            ApiRequestType.ChassisReset, "reboot",
            reset_type="On"
        )

    def test_basic_power_on_reset_type_off(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        cmd_result = manager.sync_invoke(
            ApiRequestType.ChassisReset, "reboot",
            reset_type="On"
        )
