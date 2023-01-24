"""iDRAC storage list view

Command provides the option to retrieve list of storage controllers.

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from base import CommandResult, save_if_needed
from base import IDracManager, ApiRequestType, Singleton


class StorageListView(IDracManager, scm_type=ApiRequestType.StorageListQuery,
                      name='storage_list',
                      metaclass=Singleton):
    """iDRACs REST API fetch storage list information.
    """

    def __init__(self, *args, **kwargs):
        super(StorageListView, self).__init__(*args, **kwargs)

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

        help_text = "fetch the storage devices"
        return cmd_arg, "storage_list", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Queries for storage controller list.
        :param do_async: will not block and return result as future.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:  json, xml etc.
        :param verbose: enables verbose output
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
            f"System.Embedded.1/Storage"

        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        save_if_needed(filename, data)
        return CommandResult(data, None, None)
