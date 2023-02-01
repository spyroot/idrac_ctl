"""iDRAC reset manager ,

command reset-reboot IDRAC manger.

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton


class ManagerReset(IDracManager,
                   scm_type=ApiRequestType.ManagerReset,
                   name='manager_reset',
                   metaclass=Singleton):
    """iDRAC Manager server Command, fetch manager service,
    caller can save to a file or output to a file or pass downstream.
    """

    def __init__(self, *args, **kwargs):
        super(ManagerReset, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--async', action='store_true',
                             required=False, dest="do_async",
                             default=False,
                             help="Will create a task and will not wait.")

        cmd_arg.add_argument('--graceful', action='store_true',
                             required=False, dest="do_graceful",
                             default=True, help="do graceful reset.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to "
                                  "save a respond to a file.")

        help_text = "command reboot idrac manager"
        return cmd_arg, "manager-reboot", help_text

    def execute(self, filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_graceful: Optional[bool] = True,
                **kwargs) -> CommandResult:
        """Reset reboot IDRAC manager services.
        :param do_async will not wait.
        :param do_graceful
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

        t = "/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.Reset"
        if do_graceful:
            pd = {
                "ResetType": "GracefulRestart"
            }
        else:
            pd = {}

        api_result = self.base_post(
            t, payload=pd, do_async=do_async,
            expected_status=204, verbose=verbose
        )

        if api_result.data['Status']:
            resp = self.parse_task_id(api_result)
            api_result.data.update(resp)

        return api_result
