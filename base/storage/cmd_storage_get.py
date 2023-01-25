"""iDRAC storage cmd

Command provides the option to retrieve storage information for specific
controller disk from iDRAC.

Example
python idrac_ctl.py storage-get --storage_controller NonRAID.Slot.6-1

Expanded
python idrac_ctl.py storage-get --storage_controller NonRAID.Slot.6-1 -e

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
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument('--storage_controller', required=False, type=str,
                                default="",
                                help="controller name.")

        help_text = "command fetch the storage information"
        return cmd_parser, "storage-get", help_text

    def execute(self,
                filename: Optional[str] = None,
                storage_controller: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Get storage controller details.
        :param do_expanded:
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

        target_api = f"/redfish/v1/Systems/System.Embedded.1/Storage/{storage_controller}"
        return self.base_query(target_api,
                               filename=filename,
                               do_async=do_async,
                               do_expanded=do_expanded)
