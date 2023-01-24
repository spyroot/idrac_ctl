"""iDRAC storage cmd

Command provides the option to retrieve storage information for specific
controller disk from iDRAC.

python idrac_ctl.py storage_get --storage_controller NonRAID.Slot.6-1

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from base import CommandResult, save_if_needed
from base import IDracManager, ApiRequestType, Singleton


class StorageView(IDracManager, scm_type=ApiRequestType.StorageViewQuery,
                  name='storage_get',
                  metaclass=Singleton):
    """iDRACs REST API fetch storage information.
    """

    def __init__(self, *args, **kwargs):
        super(StorageView, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)
        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        cmd_arg.add_argument('--storage_controller', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "fetch the storage information"
        return cmd_arg, "storage_get", help_text

    def execute(self,
                filename: Optional[str] = None,
                storage_controller: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Queries storage controller from iDRAC.
        :param storage_controller: if empty cmd will return list of controllers.
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:  json, xml etc.
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
            f"System.Embedded.1/Storage/{storage_controller}"

        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        save_if_needed(filename, data)
        return CommandResult(data, None, None)
