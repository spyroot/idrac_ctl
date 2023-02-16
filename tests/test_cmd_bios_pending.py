import json
import os
import pathlib
from json import JSONDecodeError
from unittest import TestCase

import idrac_ctl
from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.idrac_shared import ApiRequestType
import logging

logging.basicConfig()
log = logging.getLogger("LOG")


class TestBiosPending(TestCase):
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

    def test_basic_bios_registry_query(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.BiosQueryPending, "bios_inventory")

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, list)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except JSONDecodeError as _:
            self.fail("raised exception")

    def test_save_bios_registry_query(
            self, bios_filename="/tmp/bios_pending01.json"):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.BiosRegistry, "bios_query_pending",
            filename=bios_filename)

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, list)
        try:
            _ = json.dumps(query_result.data, sort_keys=True, indent=4)
        except JSONDecodeError as _:
            self.fail("raised exception")

        generated_file = pathlib.Path(bios_filename)
        self.assertTrue(generated_file.exists(),
                        f"cmd must save a file")

        json_file = idrac_ctl.from_json_spec(bios_filename)
        try:
            _ = json.dumps(json_file, sort_keys=True)
        except JSONDecodeError as _:
            self.fail("raised exception")

        generated_file.unlink()

    def test_save_bios_save_no_read_only(
            self, filename="/tmp/bios_pending01.json"):
        """test basic bios query and save to a file
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.BiosQueryPending, "bios_query_pending",
            filename=filename,
            no_read_only=True)

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, list)
        try:
            _ = json.dumps(query_result.data, sort_keys=True, indent=4)
        except JSONDecodeError as _:
            self.fail("raised exception")

        generated_file = pathlib.Path(filename)
        self.assertTrue(
            generated_file.exists(), "cmd must save a file")

        json_file = idrac_ctl.from_json_spec(
            filename)
        try:
            _ = json.dumps(json_file, sort_keys=True)
        except JSONDecodeError as _:
            self.fail("raised exception")

        generated_file.unlink()
