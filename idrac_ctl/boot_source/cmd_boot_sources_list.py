"""iDRAC boot options.

Command provides the option to retrieve boot source from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command
caller can save to a file and consume asynchronously or synchronously.

Doc
https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v3.3-series/
idrac9_3.36_redfishapiguide/dellbootsources?guid=guid-4803ff0e-76ad-42c5-a971-820123cd0b83&lang=en-us

python idrac_ctl.py --json boot_source

cmd return list of boot devices.

    "/redfish/v1/Systems/System.Embedded.1/BootOptions/HardDisk.List.1-1",
    "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Integrated.1-1-1",
    "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Slot.8-1",
    "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Slot.8-1",
    "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Slot.8-1",
    "/redfish/v1/Systems/System.Embedded.1/BootOptions/NIC.Slot.8-1"


Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class BootOptionsList(IDracManager, scm_type=ApiRequestType.BootOptions,
                      name='boot_sources_query',
                      metaclass=Singleton):
    """
    Command enable boot option
    """

    def __init__(self, *args, **kwargs):
        super(BootOptionsList, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument('--async', action='store_true', required=False, dest="do_async",
                                default=False, help="Will create a task and will not wait.")

        cmd_parser.add_argument('-f', '--filename', required=False, type=str,
                                default="",
                                help="filename if we need to save a respond to a file.")

        help_text = "command fetch the boot source list"
        return cmd_parser, "boot-source-list", help_text

    def execute(self, filename: [str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False, **kwargs) -> CommandResult:
        """List boot source from idrac
        :param do_async:
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Systems" \
            f"/System.Embedded.1/BootOptions?$expand=*($levels=1)"

        response = self.api_get_call(r, headers)
        data = response.json()
        extra = data
        self.default_error_handler(response)

        if 'Members' in data:
            data = data['Members']
            data = [d['@odata.id'] for d in data]

        return CommandResult(data, None, extra, None)
