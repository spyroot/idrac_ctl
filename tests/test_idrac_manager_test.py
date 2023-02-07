import logging
import os
from datetime import datetime
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager

logging.basicConfig()
log = logging.getLogger("LOG")


class BasicManagerTest(TestCase):
    redfish_api = None

    @classmethod
    def setUpClass(cls) -> IDracManager:
        redfish_api = IDracManager(idrac_ip=os.environ.get('IDRAC_IP', ''),
                                   idrac_username=os.environ.get('IDRAC_USERNAME', 'root'),
                                   idrac_password=os.environ.get('IDRAC_PASSWORD', ''),
                                   insecure=False,
                                   is_debug=False)
        return redfish_api

    def setUp(self) -> None:
        self.assertTrue(len(os.environ.get('IDRAC_IP', '')) > 0, "IDRAC_IP is none")
        self.assertTrue(len(os.environ.get('IDRAC_USERNAME', '')) > 0, "IDRAC_USERNAME is none")
        self.assertTrue(len(os.environ.get('IDRAC_PASSWORD', '')) > 0, "IDRAC_PASSWORD is none")

    def test_idrac_creds(self):
        manager = self.setUpClass()
        self.assertTrue(manager.idrac_ip == os.environ.get('IDRAC_IP', ''))
        self.assertTrue(manager.username == os.environ.get('IDRAC_USERNAME', ''))
        self.assertTrue(manager.password == os.environ.get('IDRAC_PASSWORD', ''))

    def test_idrac_idrac_members(self):
        """Expect /redfish/v1/Managers/iDRAC.Embedded.1"""
        manager = self.setUpClass()
        members = manager.idrac_members
        self.assertTrue(isinstance(members, str), "members must be str and flat")
        self.assertTrue(members == "/redfish/v1/Managers/iDRAC.Embedded.1")
        log.warning(f"Manager members return {members}")

    def test_idrac_manage_servers(self):
        """Expect /redfish/v1/Systems/System.Embedded.1"""
        manager = self.setUpClass()
        manager_server = manager.idrac_manage_servers
        current_query_counter = manager.query_counter

        log.warning(f"Members server {manager_server} query counter {current_query_counter}")
        self.assertTrue(isinstance(manager_server, str), "manage server must be string")
        self.assertTrue(len(manager_server) > 0, "failed fetch manager server, empty string")
        self.assertTrue(
            manager_server == "/redfish/v1/Systems/System.Embedded.1",
            "Expected string /redfish/v1/Systems/System.Embedded.1"
        )
        # track cache count
        updated_query_counter = manager.query_counter
        _ = manager.idrac_manage_servers
        self.assertTrue(updated_query_counter == manager.query_counter, "expect cache property")

    def test_idrac_manage_chassis(self):
        """Expect /redfish/v1/Chassis/System.Embedded.1"""
        manager = self.setUpClass()
        manage_chassis = manager.idrac_manage_chassis
        log.warning(f"Members chassis  {manage_chassis}")

        self.assertTrue(isinstance(manage_chassis, str), "manage chassis must be string")
        self.assertTrue(len(manage_chassis) > 0, "failed fetch manager server, empty string")
        self.assertTrue(
            manage_chassis == "/redfish/v1/Chassis/System.Embedded.1",
            "Expected string /redfish/v1/Chassis/System.Embedded.1"
        )

    def test_idrac_id(self):
        """Expects System.Embedded.1"""
        manager = self.setUpClass()
        idrac_id = manager.idrac_id
        self.assertTrue(isinstance(idrac_id, str), "idrac id must a string")
        self.assertTrue(len(idrac_id) > 0, "failed fetch idrac id, empty string")
        self.assertTrue(idrac_id == "System.Embedded.1", "Expected ID System.Embedded.1")
        log.warning(f"idrac_id server {idrac_id}")

    def test_idrac_time(self):
        manager = self.setUpClass()
        idrac_time = manager.idrac_current_time()
        log.warning(f"idrac time {idrac_time}")
        self.assertTrue(isinstance(idrac_time, datetime), "return wrong data type")
        self.assertTrue(len(str(idrac_time)) > 0, "failed fetch idrac idrac_time")

    def test_idrac_version_api(self):
        manager = self.setUpClass()
        is_new = manager.version_api
        self.assertTrue(is_new)

    def test_idrac_firmware(self):
        manager = self.setUpClass()
        resp = manager.idrac_firmware
        log.warning(f"idrac firmware {resp}")
        self.assertTrue(isinstance(resp, str), "return wrong data type.")
        self.assertTrue(len(resp) > 0, "failed fetch idrac idrac firmware")

    def test_idrac_last_reset(self):
        manager = self.setUpClass()
        resp = manager.idrac_last_reset()
        log.warning(f"idrac last rest time {resp}")
        self.assertTrue(isinstance(resp, datetime), "return wrong data type")
        self.assertTrue(len(str(resp)) > 0, "failed fetch idrac idrac reset time")


