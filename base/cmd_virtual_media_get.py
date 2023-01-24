"""iDRAC command return virtual media.

python idrac_ctl.py get_virtual_media

Command provides the option to retrieve virtual media from iDRAC
and serialize back to caller as JSON, YAML, or XML.
In addition, it automatically registered to the command line ctl tool.
Similarly to the rest command caller can save to a file and
consume asynchronously or synchronously.

python idrac_ctl.py get_virtual_media

- Each command return a result and list of REST Actions.
- Each command loaded based __init__ hence anyone can extend and add custom command.

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from base import CommandResult
from base import IDracManager, ApiRequestType, Singleton
from base.cmd_utils import save_if_needed


class VirtualMediaGet(IDracManager, scm_type=ApiRequestType.VirtualMediaGet,
                      name='virtual_disk_query',
                      metaclass=Singleton):
    """iDRACs REST API Virtual Disk Query Command, fetch virtual disk, caller can save
    result to a file or output stdout or pass downstream to jq etc. tools.
    """
    def __init__(self, *args, **kwargs):
        super(VirtualMediaGet, self).__init__(*args, **kwargs)

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

        help_text = "fetch the virtual media"
        return cmd_arg, "get_vm", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute command for virtual media query cmd.
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

        if self.version_api():
            r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
                f"System.Embedded.1/VirtualMedia?$expand=*($levels=1)"
        else:
            r = f"https://{self.idrac_ip}/v1/Managers/iDRAC.Embedded.1/" \
                f"VirtualMedia?$expand=*($levels=1)"

        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        save_if_needed(filename, data)
        return CommandResult(data, None, None)
