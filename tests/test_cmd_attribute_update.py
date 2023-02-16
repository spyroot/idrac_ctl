import json
import os
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_shared import RedfishJson
from idrac_ctl import save_if_needed


class TestUpdateAttribute(TestCase):
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

    def test_basic_attribute_query(self):
        """test basic query before we do any update
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.AttributesQuery, "attribute_inventory")

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, dict)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        self.assertTrue(RedfishJson.Attributes in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Attributes} key")
        self.assertTrue('AttributeRegistry' in query_result.data,
                        "Failed to fetch mandatory AttributeRegistry")
        self.assertTrue(RedfishJson.Data_id in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Data_id} key")

    def test_basic_update(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        # save query to a file and use to , query bios
        query_file_name = "/tmp/attribute_query.json"

        data_dict = {
            "Attributes": {
                "OwnerInfo.1.OwnerName": "idrac_ctl"
            }
        }

        save_if_needed(query_file_name, data_dict)

        query_result = manager.sync_invoke(
            ApiRequestType.AttributesUpdate,
            "attribute_update", from_spec=query_file_name
        )
        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, dict)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        query_result = manager.sync_invoke(
            ApiRequestType.AttributesQuery, "attribute_inventory")
