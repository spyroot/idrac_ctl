"""iDRAC bios command

Command provides the option to retrieve BIOS setting from iDRAC  and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command caller can save
to a file and consume asynchronously or synchronously.

python idrac_ctl.py --json bios --filter SystemModelName
python idrac_ctl.py --json bios --filter --filter systemmodelname
python idrac_ctl.py --json bios --filter ProcCStates

Filter by multiple attributes, note you search done case in sensitive

python idrac_ctl.py --json bios --filter systemmodelname,ProcCStates
{
    "ProcCStates": "Disabled",
    "systemmodelname": "PowerEdge R740"
}

On time boot

"OneTimeBootMode": "Disabled",
"BootMode": "Bios",

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
from abc import abstractmethod
from typing import Optional
from idrac_ctl import IDracManager, Singleton
from idrac_ctl import ApiRequestType, CommandResult
from idrac_ctl.cmd_utils import save_if_needed, find_ids
from idrac_ctl.custom_argparser.customer_argdefault import CustomArgumentDefaultsHelpFormatter


class BiosQuery(IDracManager,
                scm_type=ApiRequestType.BiosQuery,
                name='bios_inventory',
                metaclass=Singleton):
    """Bios Query Command, fetch bios data, caller can save to a file
    or output to a file or pass downstream.
    """

    def __init__(self, *args, **kwargs):
        super(BiosQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls, parent=None):
        """Registers command args
        :return:
        """
        if parent is not None:
            cmd_arg = argparse.ArgumentParser(add_help=False,
                                              parents=[parent],
                                              description="query iDRAC bios information",
                                              formatter_class=CustomArgumentDefaultsHelpFormatter)
        else:
            cmd_arg = argparse.ArgumentParser(add_help=False,
                                              description="query iDRAC bios information",
                                              formatter_class=CustomArgumentDefaultsHelpFormatter)

        # prog = None,
        # usage = None,
        # description = None,

        cmd_arg.add_argument('--async', required=False, default=False,
                             action='store_true', dest="do_async",
                             help="Will use asyncio.")

        cmd_arg.add_argument('--attr_only', required=False, default=False,
                             action='store_true', dest='attr_only',
                             help="Will only show attributes.")

        cmd_arg.add_argument('--filter', required=False, type=str, dest="attr_filter",
                             metavar="BIOS_ATTRIBUTE",
                             help="will filter on bios attribute information. "
                                  "Example --filter ProcCStates , "
                                  "will filter and and show C-State.")

        cmd_arg.add_argument('--deep', default=False, required=False, action='store_true',
                             dest="do_deep", help="deep walk. will make a separate "
                                                  "rest api call for each discovered api.")

        cmd_arg.add_argument('-f', '--filename', required=False, default="",
                             type=str,
                             help="filename if we need to save a respond to a file.")

        help_text = "command fetch the bios information"
        return cmd_arg, "bios", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                attr_only: Optional[bool] = False,
                attr_filter: Optional[str] = "",
                **kwargs) -> CommandResult:
        """Query bios from iDRAC.

        :param attr_filter: filters by BIOS attributes.
        :param attr_only: Will only output attribute i.e. current bios settings.
        :param do_async: will use asyncio
        :param verbose: verbose output, mainly for debug.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param do_deep: deep walk
        :param data_type: default json
        :return:
        """
        idrac_api = "/redfish/v1/Systems/System.Embedded.1/Bios"

        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"do_deep:{do_deep} do_async:{do_async} "
                  f"attr_filter:{attr_filter}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r: str = f"https://{self.idrac_ip}{idrac_api}"
        if not do_async:
            response = self.api_get_call(r, headers)
            self.default_error_handler(response)
        else:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))

        data = response.json()
        # list of action for bios
        action_dict = self.discover_redfish_actions(self, data)
        if attr_only is True and 'Attributes' in data:
            data = {'Attributes': data['Attributes']}

        # filter
        data = self.filter_attribute(self, data, attr_filter)

        # save data
        save_if_needed(filename, data)

        extra_data_dict = {}
        if do_deep:
            api_links = find_ids(data, "@odata.id")
            api_links = [u for u in api_links if idrac_api != u]
            for api_link in api_links:
                r = f"https://{self.idrac_ip}{api_link}"
                if not do_async:
                    response = self.api_get_call(r, headers)
                    self.default_error_handler(response)
                else:
                    loop = asyncio.get_event_loop()
                    response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))

                extra_data_dict[api_link] = response.json()

        for d in extra_data_dict.values():
            act = self.discover_redfish_actions(self, d)
            action_dict.update(act)

        return CommandResult(data, action_dict, extra_data_dict)
