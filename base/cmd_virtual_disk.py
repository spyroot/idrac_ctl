"""iDRAC virtual disk query command

Command provides the option to retrieve virtual disk from iDRAC
and serialize back to caller as JSON, YAML, or XML. In addition, it automatically
registered to the command line ctl tool. Similarly to the rest command caller can save
to a file and consume asynchronously or synchronously.

- Each command return a result and list of REST Actions.
- Each command loaded based __init__ hence anyone can extend and add custom command.

"RAID.Mezzanine.1-1"
"RAID.SL.3-1"
"Disk.Bay.2:Enclosure.Internal.0-1:RAID.Mezzanine.1-1"

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from base import CommandResult
from base import IDracManager, ApiRequestType, Singleton
from cmd_utils import save_if_needed


class VirtualDiskQuery(IDracManager, scm_type=ApiRequestType.VirtualDiskQuery,
                       name='virtual_disk_query',
                       metaclass=Singleton):
    """iDRACs REST API Virtual Disk Query Command, fetch virtual disk, caller can save
    result to a file or output stdout or pass downstream to jq etc tools.
    """

    def __init__(self, *args, **kwargs):
        super(VirtualDiskQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--deep', action='store_true', required=False,
                             default=False,
                             help="deep walk. will make separate rest call "
                                  "for rest action discovered during initial call.")

        cmd_arg.add_argument('-s', '--save_all', required=False, type=str, dest="do_save",
                             default=bool, help="for deep walk by default we don't "
                                                "save result to a file. save_all "
                                                "will save to a separate file.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "fetch the virtual disk data"
        return cmd_arg, "attribute", help_text

    def execute(self, filename: str, virtual_disks,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Queries virtual disk from iDRAC.
        :param virtual_disks:
        :param verbose: enables verbose output
        :param do_deep: do deep recursive fetch
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
            f"System.Embedded.1/Storage/{virtual_disks}/Volumes"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()

        virtual_disk_list = []
        if not data['Members']:
            return CommandResult(None, None, None)
        else:
            virtual_disk_list = [i['@odata.id'].split("/")[-1] for i in data['Members']]

        for ii in virtual_disk_list:
            r = f"https://{self.idrac_ip}/redfish/v1/Systems/System.Embedded.1/Storage/Volumes/{ii}"
            response = self.api_get_call(r, headers)
            resp_data = response.json()
            for i in resp_data.items():
                if i[0] == "VolumeType":
                    print("%s, Volume type: %s" % (ii, i[1]))

        save_if_needed(filename, data)
        return CommandResult()
