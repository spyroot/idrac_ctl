"""iDRAC reset a power state for compute system command.

This action is used to reset the system.
Command provides the option to reboot, and change power state.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import json
import warnings
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton, CommandResult, UnexpectedResponse
from idrac_ctl.cmd_exceptions import InvalidArgument


class RebootHost(IDracManager,
                 scm_type=ApiRequestType.RebootHost,
                 name='reboot',
                 metaclass=Singleton):
    """
    "Actions": {
        "#ComputerSystem.Reset": {
            "ResetType@Redfish.AllowableValues": [
                "On",
                "ForceOff",
                "ForceRestart",
                "GracefulRestart",
                "GracefulShutdown",
                "PushPowerButton",
                "Nmi",
                "PowerCycle"
            ],
            "target": "/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset"
        }
    },
    """
    def __init__(self, *args, **kwargs):
        super(RebootHost, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument('--reset_type',
                                required=False, dest='reset_type',
                                default="GracefulRestart", type=str,
                                help="Reset On, ForceOff, "
                                     "ForceRestart, GracefulRestart, "
                                     "GracefulShutdown, "
                                     "PushPowerButton, Nmi, PowerCycle.")

        cmd_parser.add_argument('-a', '--async', action='store_true',
                                required=False, dest="do_async",
                                default=False, help="will use async call.")

        help_text = "reboots the system"
        return cmd_parser, "reboot", help_text

    def execute(self,
                filename: Optional[str] = "",
                data_type: Optional[str] = "json",
                reset_type: Optional[str] = "On",
                power_state: Optional[str] = "On",
                boot_source_override: Optional[str] = "",
                boot_source_override_enabled: Optional[str] = "",
                boot_source_override_mode: Optional[str] = "",
                interface_type: Optional[str] = "",
                do_async: Optional[bool] = False,
                **kwargs
                ) -> CommandResult:
        """
        :param do_async:
        :param filename:
        :param data_type:
        :param reset_type: "On, ForceOff, ForceRestart, GracefulShutdown, PushPowerButton, Nmi"
        :param power_state: On, null
        :param boot_source_override: "None, Pxe, Floppy,
                                      Cd, Hdd, BiosSetup, Utilities,
                                      UefiTarget, SDCard, UefiHttp"
        :param boot_source_override_enabled: "Once, Continuous, Disabled"
        :param boot_source_override_mode: UEFI, Legacy
        :param interface_type: TCM1_0, TPM2_0, TPM1_
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        system_state = self.sync_invoke(ApiRequestType.SystemQuery, "system_query")
        system_actions = system_state.data['Actions']
        allowed_reset_types = []

        default_target = "/redfish/v1/Systems/System.Embedded.1" \
                         "/Actions/ComputerSystem.Reset"

        if '#ComputerSystem.Reset' in system_actions:
            ra = system_actions['#ComputerSystem.Reset']
            allowed_reset_types = ra['ResetType@Redfish.AllowableValues']
            if 'target' in ra:
                target = ra['target']
        else:
            target = default_target

        if reset_type not in allowed_reset_types:
            raise InvalidArgument(f"Invalid reset type"
                                  f" {reset_type}, "
                                  f"supported reset types "
                                  f"{allowed_reset_types}")

        r = f"https://{self.idrac_ip}{target}"
        payload = {
            'ResetType': reset_type
        }

        if not do_async:
            response = self.api_post_call(
                r, json.dumps(payload), headers
            )
            ok = self.default_post_success(self, response)
        else:
            loop = asyncio.get_event_loop()
            ok, response = loop.run_until_complete(
                self.async_post_until_complete(
                    r, json.dumps(payload), headers
                )
            )

        try:
            job_id = self.job_id_from_header(response)
            if job_id is not None:
                self.fetch_job(job_id)
        except UnexpectedResponse as ur:
            self.logger.error(ur)

        return CommandResult(self.api_success_msg(ok), None, None)
