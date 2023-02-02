"""iDRAC enable boot options.

This cmd return Dell Boot Sources Configuration and the related
resources.

Command provides the option to retrieve boot source from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command
caller can save to a file and consume asynchronously or synchronously.


Author Mus spyroot@gmail.com
"""
import json

from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult
from idrac_ctl.cmd_exceptions import InvalidArgument, UnexpectedResponse


class BootOneShot(IDracManager,
                  scm_type=ApiRequestType.BootOneShot,
                  name='boot_one_shot',
                  metaclass=Singleton):
    """
    Command enable boot option
    """

    def __init__(self, *args, **kwargs):
        super(BootOneShot, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_reboot=True, is_expanded=False)

        cmd_parser.add_argument('--device', required=False, type=str,
                                default="Cd",
                                help="boot device Pxe,Cd,Hdd,BiosSetup,UefiTarget,SDCard etc")

        cmd_parser.add_argument('--power_on', action='store_true',
                                required=False, dest="do_power_on",
                                help="will power on a chassis., if current state in power-down.")

        cmd_parser.add_argument('--uefi_target', required=False, type=str,
                                default=None,
                                help="uefi_target")

        help_text = "command change one shoot boot"
        return cmd_parser, "boot-one-shot", help_text

    def execute(self,
                device: Optional[str] = None,
                uefi_target: Optional[str] = None,
                do_check: Optional[str] = None,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_reboot: Optional[bool] = False,
                do_power_on: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query information for particular boot source device from idrac.
        Example python idrac_ctl.py get_boot_source --dev "HardDisk.List.1-1"

        VenHw(986D1755-B9D0-4F8D-A0DA-D1DB18672045)

        :param do_reboot:  will reboot host
        :param do_power_on: will power on server.
        :param uefi_target:
        :param device:  get the list of supported device.
                        For example None, Pxe,Cd,Hdd,BiosSetup,UefiTarget,SDCard,UefiHttp
        :param do_check:
        :param do_async: note async will subscribe to an event loop.
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"do_async:{do_async} filename:{filename}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        # power on first if a client requested.
        if do_power_on:
            current_boot = self.sync_invoke(
                ApiRequestType.ChassisReset,
                "reboot",
                reset_type="On"
            )

        current_boot = self.sync_invoke(
            ApiRequestType.CurrentBoot,
            "current_boot_query"
        )
        boot_device = current_boot.data['BootSourceOverrideTarget@Redfish.AllowableValues']
        if device not in boot_device:
            raise InvalidArgument(f"Invalid boot device {device}, "
                                  f"supported device {boot_device}")

        if uefi_target is not None:
            current_boot = self.sync_invoke(
                ApiRequestType.BootOptions, "boot_sources_query"
            )
            uefi_devs = [d['UefiDevicePath'] for d
                         in current_boot.extra['Members'] if 'UefiDevicePath' in d]
            if uefi_target not in uefi_devs:
                raise InvalidArgument(f"Invalid uefi device path {uefi_target},"
                                      f" supported uefi devices {boot_device}")

        payload = {
            "Boot": {
                "BootSourceOverrideTarget": device,
                "UefiTargetBootSourceOverride": uefi_target
            }
        }

        r = f"https://{self.idrac_ip}/redfish/v1/Systems/System.Embedded.1"
        for key, value in dict(payload['Boot']).items():
            if value is None:
                del payload['Boot'][key]

        response = self.api_patch_call(r, json.dumps(payload), headers)
        api_result = {}
        if self.default_patch_success(self, response):
            api_result = self.api_success_msg(True)

        try:
            json_data = response.json()
            if verbose:
                self.default_json_printer(json_data)
            job_id = self.job_id_from_header(response)
            if job_id is not None:
                data = self.fetch_job(job_id)
                api_result.update(data)
        except UnexpectedResponse as ur:
            self.logger.critical(ur, exc_info=True)
            pass

        if do_reboot:
            reboot_result = self.reboot()
            api_result.update(reboot_result)

        return CommandResult(api_result, None, None)
