"""iDRAC reset a chassis power state.

python idrac_ctl.py chassis-reset --reset_type ForceOff

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl import CommandResult
from idrac_ctl.cmd_exceptions import UnexpectedResponse


class ChangeBootOrder(IDracManager,
                      scm_type=ApiRequestType.ChangeBootOrder,
                      name='change_boot_order',
                      metaclass=Singleton):
    """Command change boot order.
    """

    def __init__(self, *args, **kwargs):
        super(ChangeBootOrder, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_file_save=False, is_expanded=False)
        cmd_parser.add_argument('--boot_order',
                                required=False, dest='reset_type',
                                default="", type=str,
                                help="Coma seperated list. Example HardDisk.List.1-1,NIC.Integrated.1-1-1")

        help_text = "command change boot order"
        return cmd_parser, "change-boot-order", help_text

    def execute(self,
                boot_order: str,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_async: Optional[bool] = False,
                **kwargs
                ) -> CommandResult:
        """
        "Boot": {
        "BootOptions": {
            "@odata.id": "/redfish/v1/Systems/System.Embedded.1/BootOptions"
        },
        "BootOrder": [
            "HardDisk.List.1-1",
            "NIC.Integrated.1-1-1",
            "NIC.Slot.8-1",
            "NIC.Slot.8-1",
            "NIC.Slot.8-1",
            "NIC.Slot.8-1",
            "Optical.iDRACVirtual.1-1"
        ],
        "BootOrder@odata.count": 7,
        "BootSourceOverrideEnabled": "Disabled",
        "BootSourceOverrideMode": "Legacy",
        "BootSourceOverrideTarget": "None",
        "BootSourceOverrideTarget@Redfish.AllowableValues": [
            "None",
            "Pxe",
            "Floppy",
            "Cd",
            "Hdd",
            "BiosSetup",
            "Utilities",
            "UefiTarget",
            "SDCard",
            "UefiHttp"
        ],
        "Certificates": {
            "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Boot/Certificates"
        },
        "UefiTargetBootSourceOverride": null

        :param boot_order:
        :param filename:
        :param do_async:
        :param data_type:
        :param kwargs:
        :return: return cmd result
        :raise FailedDiscoverAction
        """
        target_api = "/redfish/v1/Systems/System.Embedded.1/Bios"
        cmd_query = self.base_query(
            target_api, filename=filename,
            do_async=do_async, do_expanded=False
        )
        if cmd_query.error is not None:
            return cmd_query

        current_boot_mode = cmd_query.data['Attributes']['SetBootOrderEn']
        self.logger.info("Current boot mode", current_boot_mode)

        if boot_order is not None:
            boot_order = boot_order.strip().split(",")

        payload = {
            "Boot": {
                "BootOrder": boot_order
            }
        }

        target_patch_api = "/redfish/v1/Systems/System.Embedded.1"
        api_result = self.base_patch(
            target_patch_api, payload=payload,
            do_async=do_async, expected_status=202)

        if api_result.error is not None:
            return api_result

        if api_result.extra is not None:
            resp = api_result.extra
            try:
                job_id = self.parse_task_id(resp)
                if job_id is not None:
                    api_result.data = self.fetch_job(job_id)
            except UnexpectedResponse as ur:
                self.logger.error(ur)
                api_result.error = ur

        return api_result
