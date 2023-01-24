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
from abc import abstractmethod
from typing import Optional
from base import IDracManager, Singleton
from base import ApiRequestType, CommandResult
from base.cmd_utils import save_if_needed


class BiosQuery(IDracManager, scm_type=ApiRequestType.BiosQuery,
                name='bios_inventory',
                metaclass=Singleton):
    """Bios Query Command, fetch bios data, caller can save to a file
    or output to a file or pass downstream.
    """

    def __init__(self, *args, **kwargs):
        super(BiosQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--async', action='store_true', required=False, dest="do_async",
                             default=False, help="Will create a task and will not wait.")

        cmd_arg.add_argument('--attr_only', action='store_true', default=False,
                             required=False, dest='attr_only',
                             help="will show only attributes.")

        cmd_arg.add_argument('--filter', required=False, type=str, dest="attr_filter",
                             help="Filter on bios attribute information. "
                                  "Example --filter ProcCStates , "
                                  "will filter and and show C-State.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "fetch the bios information"
        return cmd_arg, "bios", help_text

    # ProcCStates
    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                attr_only: Optional[bool] = False,
                attr_filter: Optional[str] = "",
                **kwargs) -> CommandResult:
        """Query bios from idrac

        :param attr_filter: Filters by attributes,
        :param attr_only: Will only output attribute i.e. current bios settings.
        :param do_deep:
        :param do_async:
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:
        :return:
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"do_deep:{do_deep} do_async:{do_async} attr_filter:{attr_filter}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)
        r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
            f"System.Embedded.1/Bios"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()

        # list of action for bios
        action_dict = self.discover_redfish_actions(self, data)
        if attr_only is True and 'Attributes' in data:
            data = {'Attributes': data['Attributes']}

        # filter
        data = self.filter_attribute(self, data, attr_filter)

        # save data
        save_if_needed(filename, data)

        return CommandResult(data, action_dict, None)
