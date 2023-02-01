"""iDRAC boot query command

Command provides the option to retrieve boot source from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command
caller can save to a file and consume asynchronously or synchronously.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType
from idrac_ctl import IDracManager, CommandResult
from idrac_ctl.cmd_utils import save_if_needed, find_ids


class BootQuery(IDracManager,
                scm_type=ApiRequestType.BootQuery,
                name='boot_query',
                metaclass=Singleton):
    """
    Command return boot source
    """
    def __init__(self, *args, **kwargs):
        super(BootQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)
        cmd_arg.add_argument('--async', action='store_true',
                             required=False, dest="do_async",
                             default=False,
                             help="Will use asyncio.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        cmd_arg.add_argument('--deep', action='store_true', required=False, dest="do_deep",
                             default=False, help="deep walk. will make a separate "
                                                 "rest call for each discovered api.")

        help_text = "command fetch the boot source"
        return cmd_arg, "boot", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query boot source from idrac
        :param do_async: will use asyncio
        :param verbose:
        :param do_deep:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Systems" \
            f"/System.Embedded.1/BootSources"

        if not do_async:
            response = self.api_get_call(r, headers)
            self.default_error_handler(response)
        else:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self.api_async_get_until_complete(r, headers)
            )

        data = response.json()
        save_if_needed(filename, data)

        # extra data
        extra_actions = find_ids(data, "@odata.id")
        extra_data = None
        if do_deep:
            extra_data = [self.api_get_call(f"https://{self.idrac_ip}{a}", headers).json()
                          for a in extra_actions]

        return CommandResult(data, None, extra_data)
