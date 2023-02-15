import json
import os
from unittest import TestCase
from idrac_ctl.idrac_manager import IDracManager, CommandResult
from idrac_ctl.idrac_shared import ApiRequestType
from idrac_ctl.redfish_shared import RedfishJson


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

    def test_basic_accounts_query(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.QueryAccounts, "attribute_inventory")

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, dict)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        self.assertTrue(RedfishJson.Members in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Members} key")
        self.assertTrue(RedfishJson.Data_id in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Data_id} key")
        self.assertTrue(RedfishJson.Data_content in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Data_content} key")

    def test_basic_accounts_query_expanded(self):
        """test basic query
        :return:
        """
        manager = self.setUpClass()
        query_result = manager.sync_invoke(
            ApiRequestType.QueryAccounts, "attribute_inventory")

        self.assertIsInstance(query_result, CommandResult)
        self.assertIsInstance(query_result.data, dict)
        try:
            json.dumps(query_result.data, sort_keys=True, indent=4)
        except Exception as _:
            self.fail("raised exception")

        self.assertTrue(RedfishJson.Members in query_result.data,
                        f"Failed to fetch mandatory {RedfishJson.Members} key")

        members_data = query_result.data[RedfishJson.Members]
        self.assertTrue(RedfishJson.Members in members_data,
                        f"Failed to fetch mandatory {RedfishJson.Members} "
                        f"key from member data")

        members_data = query_result.data[RedfishJson.Members]
        self.assertIsInstance(members_data, list)

        self.assertTrue(RedfishJson.MembersCount in members_data,
                        f"Failed to fetch mandatory {RedfishJson.MembersCount} "
                        f"key from member data")

        member_count = int(RedfishJson.MembersCount)
        self.assertTrue(len(members_data) == member_count,
                        f"member count and len of list must match")
    #
    # def test_basic_base_expanded_query(self):
    #     """test basic query
    #     :return:
    #     """
    #     manager = self.setUpClass()
    #     query_result = manager.sync_invoke(
    #         ApiRequestType.QueryAccounts, "attribute_inventory", filename="")
    #
    #     self.assertIsInstance(query_result, CommandResult)
    #     self.assertIsInstance(query_result.data, dict)
    #     try:
    #         json.dumps(query_result.data, sort_keys=True, indent=4)
    #     except Exception as _:
    #         self.fail("raised exception")
    #
    #     self.assertTrue(RedfishJson.Members in query_result.data,
    #                     f"Failed to fetch mandatory {RedfishJson.Members} key")
    #
    #     members_data = query_result.data[RedfishJson.Members]
    #     self.assertTrue(RedfishJson.Members in members_data,
    #                     f"Failed to fetch mandatory {RedfishJson.Members} key from member data")
    #
    #     members_data = query_result.data[RedfishJson.Members]
    #     self.assertIsInstance(members_data, list)
    #
    #     self.assertTrue(RedfishJson.MembersCount in members_data,
    #                     f"Failed to fetch mandatory {RedfishJson.MembersCount} key from member data")
    #
    #     member_count = int(RedfishJson.MembersCount)
    #     self.assertTrue(len(members_data) == member_count,
    #                     f"member count and len of list must match")

