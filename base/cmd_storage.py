"""iDRAC storage controller query

Command provides the option to retrieve storage controller information
from iDRAC and serialize back as caller as JSON, YAML, or XML. In addition,
it automatically registered to the command line ctl tool. Similarly to
the rest command caller can save to a file and consume asynchronously
or synchronously.

On return will hold list of controller in CommandResult.data

['NonRAID.Slot.6-1',
'AHCI.Embedded.1-1',
 'AHCI.Slot.4-1',
 'AHCI.Embedded.2-1']

python idrac_ctl.py storage

Example: filter by controller type
idrac_ctl.py --json storage --filter AHCI

[
    "AHCI.Embedded.1-1",
    "AHCI.Slot.4-1",
    "AHCI.Embedded.2-1"
]

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional, Tuple

from base import Singleton, ApiRequestType, IDracManager, save_if_needed, CommandResult


class StorageQuery(IDracManager, scm_type=ApiRequestType.StorageQuery,
                   name='storage_query',
                   metaclass=Singleton):
    """
    Command return storage controller
    """

    def __init__(self, *args, **kwargs):
        super(StorageQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls) -> Tuple[argparse.ArgumentParser, str, str]:
        """Register command and all command optional flags.
        :param cls:
        :return: tuple ArgumentParser, command name, help_text
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)
        cmd_arg.add_argument('--async', action='store_true', required=False, dest="do_async",
                             default=False, help="Will create a task and will not wait.")

        cmd_arg.add_argument('-s', '--save_all', required=False, type=str, dest="do_save",
                             default=False,
                             help="for deep walk by default we don't "
                                  "save result to a file. save_all "
                                  "will save to a separate file.")

        cmd_arg.add_argument('--filter', required=False, type=str, dest="id_filter",
                             help="Filter on controller information. "
                                  "Example --filter AHCI , "
                                  "will filter and only AHCI controllers")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "fetch the storage information"
        return cmd_arg, "storage", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                id_filter: Optional[str] = "",
                **kwargs) -> CommandResult:
        """Query storage controller from idrac.

        Example of members

        "Members": [
        {"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/NonRAID.Slot.6-1"},
        {"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.1-1"},
        {"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Slot.4-1"},
        {"@odata.id": "/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.2-1"}

        On return will hold list of controller in
        CommandResult.data
        ['NonRAID.Slot.6-1', 'AHCI.Embedded.1-1', 'AHCI.Slot.4-1', 'AHCI.Embedded.2-1']

        CommandResult.discovered
        ['/redfish/v1/Systems/System.Embedded.1/Storage/NonRAID.Slot.6-1',
        '/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.1-1',
        '/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Slot.4-1',
        '/redfish/v1/Systems/System.Embedded.1/Storage/AHCI.Embedded.2-1']

        :param verbose: do a verbose output
        :param do_async: will not block
        :param data_type: json or xml
        :param id_filter: a filter a storage controller i.e. filter @id_filter
        :param filename: if filename indicate call will save a bios setting to a file.
        :param do_deep: do deep walk for each controller.
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"do_deep:{do_deep} do_async:{do_async} id_filter:{id_filter}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)
        r = f"https://{self.idrac_ip}/redfish/v1/Systems" \
            f"/System.Embedded.1/Storage"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        save_if_needed(filename, data)

        controller_list = [id_data['@odata.id'].split("/")[-1] for id_data in data['Members']
                           if id_filter is not None and len(id_filter) > 0
                           and id_filter in id_data['@odata.id']]
        controller_uri = [id_data['@odata.id'] for id_data in data['Members']
                          if id_filter is not None and len(id_filter) > 0
                          and id_filter in id_data['@odata.id']]

        return CommandResult(controller_list, controller_uri, None)
