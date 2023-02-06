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
import warnings
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult, save_if_needed, InvalidArgument
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.idrac_manager import ResourceNotFound


class VirtualDiskQuery(IDracManager, scm_type=ApiRequestType.VirtualDiskQuery,
                       name='virtual_disk_query',
                       metaclass=Singleton):
    """iDRACs REST API Virtual Disk Query Command, fetch virtual disk, caller can save
    result to a file or output stdout or pass downstream to jq etc. tools.
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
        cmd_arg.add_argument('--device_id', required=False, type=str,
                             default="", help="storage device id. "
                                              "Example NonRAID.Slot.6-1.")

        cmd_arg.add_argument('-f', '--filename', required=False, type=str,
                             default="",
                             help="filename if we need to save a respond to a file.")

        help_text = "fetch the virtual disk data"
        return cmd_arg, "volumes", help_text

    def execute(self,
                filename: Optional[str] = None,
                device_id: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Queries volumes from given controlled from iDRAC.
        :param device_id: a storage controller id, NonRAID.Slot.6-1
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

        storage_id = self.sync_invoke(ApiRequestType.StorageListQuery,
                                      "storage_list")
        storage_members = storage_id.data['Members']
        storage_ids = [k['@odata.id'].split("/")[-1]
                       for k in storage_members if '@odata.id' in k]

        if device_id not in storage_ids:
            raise InvalidArgument(f"Storage device_id {device_id} "
                                  "not found, available {storage_ids}")

        r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
            f"System.Embedded.1/Storage/{device_id}/Volumes"
        #
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()

        vd_list = []
        if not data['Members']:
            return CommandResult(None, None, None, None)
        else:
            vd_list = [i['@odata.id'].split("/")[-1] for i in data['Members']]

        for vol_id in vd_list:
            r = f"https://{self.idrac_ip}/redfish/v1/Systems" \
                f"/System.Embedded.1/Storage/Volumes/{vol_id}"
            try:
                response = self.api_get_call(r, headers)
                self.default_error_handler(response)
            except ResourceNotFound as exp:
                warnings.warn(str(exp))
                continue
                pass
            resp_data = response.json()
            vd_list.append(resp_data)

        save_if_needed(filename, data)
        return CommandResult(vd_list, None, None, None)
