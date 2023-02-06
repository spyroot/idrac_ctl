"""iDRAC

The ConvertToNonRAID() method is used to convert a physical disks in
RAID state of "Ready" to a Non-RAID state.

After the method is successfully executed, the
DCIM_PhysicalDiskView.RAIDStatus property of that physical
disk should reflect the new state.

python idrac_ctl.py storage-convert-noraid -c AHCI.Embedded.2-1

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult, find_ids
from idrac_ctl import IDracManager, ApiRequestType, Singleton


class ConvertToRaid(IDracManager,
                    scm_type=ApiRequestType.ConvertToRaid,
                    name='convert_none_raid',
                    metaclass=Singleton):
    """iDRACs REST API convert none raid disk to raid
    for a target controller.
    """
    def __init__(self, *args, **kwargs):
        super(ConvertToRaid, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument('-c', '--controller', required=False, type=str,
                                default="",
                                help="controller name.")

        cmd_parser.add_argument('--exclude', required=False,
                                type=str, dest="exclude_filter",
                                default="", help="Exclude disk or disks "
                                                 "Disk.Direct.0-0:AHCI.Embedded.2-1")

        help_text = "command converts none raid disk under controller to raid"
        return cmd_parser, "storage-convert-raid", help_text

    def execute(self,
                controller: Optional[str] = None,
                exclude_filter: Optional[str] = None,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Command convert none raid disk to raid if supported.

        :param exclude_filter:  excluded disk or command separate disks
        :param controller: if empty cmd will return list of controllers.
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:  json, xml etc.
         :param do_expanded:
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        drives = self.sync_invoke(ApiRequestType.StorageViewQuery,
                                  "storage_get", controller=controller,
                                  data_filter="Drives")

        odata_ids = find_ids(drives.data, "@odata.id")
        final_data = []
        disk_ids = {}

        raid_disk_ids = []
        none_raid_disk_ids = []
        for oids in odata_ids:
            disk_id = oids.split("/")[-1]
            disk_ids[disk_id] = oids
            cmd_rest = self.base_query(oids,
                                       filename=None,
                                       do_async=do_async,
                                       do_expanded=do_expanded)
            if 'Oem' in cmd_rest.data:
                oem = cmd_rest.data['Oem']
                if 'Dell' in oem:
                    raid_status = oem['Dell']['DellPhysicalDisk']['RaidStatus']
                    if 'NonRAID' in raid_status:
                        none_raid_disk_ids.append(disk_id)
                    else:
                        raid_disk_ids.append(disk_id)

            final_data.append(cmd_rest.data)

        final_data.append({"disk_ids": disk_ids})
        final_data.append({"none_raid_disk_ids": none_raid_disk_ids})
        final_data.append({"raid_disk_ids": raid_disk_ids})

        target_api = "/redfish/v1/Dell/Systems/System.Embedded.1/DellRaidService" \
                     "/Actions/DellRaidService.ConvertToRAID"

        if len(none_raid_disk_ids) > 0:
            none_raid_disk_ids = [x for x in none_raid_disk_ids if x not in exclude_filter]
            payload = {"PDArray": none_raid_disk_ids}
            cmd_result = self.base_post(target_api, payload, do_async=do_async)
            resp = self.parse_task_id(cmd_result)
            cmd_result.data.update(resp)
            return CommandResult(cmd_result.data, None, None, None)

        return CommandResult({"Status": "all disk are none raid"}, None, None, None)
