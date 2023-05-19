"""iDRAC query command

Command provides capability raw query based URI resource,
in case specific action might not implement yet; hence it
is easy to query.

Author Mus spyroot@gmail.com
"""
import json
import os
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from ..idrac_manager import IDracManager
from ..idrac_shared import ApiRequestType
from ..idrac_shared import Singleton
from ..redfish_exceptions import RedfishForbidden
from ..redfish_manager import CommandResult


class Discovery(IDracManager,
                scm_type=ApiRequestType.Discovery,
                name='discovery_idrac',
                metaclass=Singleton):
    """A command query iDRAC resource based on a resource path.
    """

    def __init__(self, *args, **kwargs):
        super(Discovery, self).__init__(*args, **kwargs)
        self.visited_urls = {}
        home_dir = str(Path.home())
        redfish_ip = self.redfish_ip.replace(":", "")
        self.json_response_dir = f"{str(home_dir)}/.json_responses/{redfish_ip}"

        self.default_query_filter = ["LogServices/Sel/Entries",
                                     "JID_",
                                     "StdSecbootpolicy.",
                                     "Signatures/StdSecbootpolicy.",
                                     "Lclog/Entries/"]

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command discovery all action."
        return cmd_parser, "discovery", help_text

    def extract_odata_ids(self, data):
        """

        :param data:
        :return:
        """

        if isinstance(data, dict):
            odata_id = data.get("@odata.id")
            if odata_id:
                yield odata_id
            for value in data.values():
                yield from self.extract_odata_ids(value)
        elif isinstance(data, list):
            for item in data:
                yield from self.extract_odata_ids(item)

    def recursive_discovery(self, resource_path):
        """
        :param resource_path:
        :return:
        """
        for query_filter in self.default_query_filter:
            if query_filter in resource_path:
                self.visited_urls[resource_path] = True
                return

        if resource_path in self.visited_urls or not resource_path.startswith("/redfish/v1"):
            return

        if resource_path in self.visited_urls:
            return

        try:
            result = self.base_query(resource_path)
            print("Discovery: {}".format(resource_path))

            self.visited_urls[resource_path] = True
            response_filename = os.path.join(
                self.json_response_dir, resource_path.replace("/", "_") + ".json")

            with open(response_filename, "w") as file:
                json.dump(result.data, file, indent=4)

            odata_ids = list(self.extract_odata_ids(result.data))

            for r in odata_ids:
                # self.visited_urls[r] = True
                self.recursive_discovery(r)
        except RedfishForbidden as e:
            self.visited_urls[resource_path] = True
            print("Forbidden: {}".format(e))
        except Exception as other_err:
            self.visited_urls[resource_path] = True
            print("Forbidden: {}".format(other_err))

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes discovery action command
        python idrac_ctl discovery

        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """

        os.makedirs(self.json_response_dir, exist_ok=True)

        result = self.base_query("/redfish/v1/",
                                 filename=filename,
                                 do_async=do_async,
                                 do_expanded=do_expanded)

        self.visited_urls["/redfish/v1/"] = True
        self.visited_urls["/redfish/v1/CompositionService"] = True
        odata_ids = list(self.extract_odata_ids(result.data))
        for r in odata_ids:
            self.recursive_discovery(r)

        # print("Result: ", result)
        return result
