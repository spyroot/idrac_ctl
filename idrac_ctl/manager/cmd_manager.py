"""iDRAC manager command

Command provides the option to retrieve iDRAC manager view.
idrac_ctl manager

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional
from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton


class Manager(IDracManager,
              scm_type=ApiRequestType.ManagerQuery,
              name='manager_query',
              metaclass=Singleton):
    """iDRAC Manager server Command, fetch manager service,
    caller can save to a file or output to a file or pass downstream.
    """
    def __init__(self, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--async', action='store_true', required=False, dest="do_async",
                             default=False, help="Will create a task and will not wait.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "command fetch the manager view"
        return cmd_arg, "manager", help_text

    def execute(self, filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Queries manager services from iDRAC.
        :param do_async:
        :param verbose:
        :param do_deep:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:
        :return:
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Managers/iDRAC.Embedded.1"
        response = self.api_get_call(r, headers)
        data = response.json()
        redfish_actions = self.discover_redfish_actions(self, data)
        return CommandResult(data, redfish_actions, None)
