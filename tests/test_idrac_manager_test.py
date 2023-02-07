import os
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager


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

    def test_idrac_id(self):
        manager = self.setUpClass()
        idrac_id = manager.idrac_id()
        self.assertTrue(len(idrac_id) > 0, "failed fetch idrac id")

    def test_idrac_time(self):
        manager = self.setUpClass()
        idrac_time = manager.idrac_current_time()
        self.assertTrue(len(idrac_time) > 0, "failed fetch idrac idrac_time")
