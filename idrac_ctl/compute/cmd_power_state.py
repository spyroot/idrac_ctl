"""iDRAC reset a power state for compute system command.

This action is used to reset the system.
Command provides the option to reboot, and change power state.

Author Mus spyroot@gmail.com
"""
import argparse
import time
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.cmd_exceptions import InvalidArgument, MissingResource
from idrac_ctl.idrac_shared import CliJobTypes, IDRAC_API, IdracApiRespond
from idrac_ctl.redfish_exceptions import RedfishException
from idrac_ctl.redfish_manager import CommandResult


class RebootHost(IDracManager,
                 scm_type=ApiRequestType.ComputerSystemReset,
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
        cmd_parser.add_argument(
            '--reset_type',
            required=False, dest='reset_type',
            default="GracefulRestart", type=str,
            help="Reset On, ForceOff, "
                 "ForceRestart, GracefulRestart, "
                 "GracefulShutdown, "
                 "PushPowerButton, Nmi, PowerCycle.")

        cmd_parser.add_argument(
            '-a', '--async', action='store_true',
            required=False, dest="do_async",
            default=False, help="will use async call.")

        cmd_parser.add_argument(
            '-w', '--wait', action='store_true',
            required=False, dest="do_wait",
            default=False, help="wait for reboot.")

        help_text = "reboots the system"
        return cmd_parser, "reboot", help_text

    def wait_for_reboot(self, sleep_time, max_retry):
        """If we need wait or graceful shutdown.  It will wait for reboot task
        and wait for reboot to complete. It makes sense to call this method
        only if reset already called.

        :param sleep_time:
        :param max_retry:
        :return:
        """
        _reboot = 1
        retry_counter = 0
        while _reboot != 0:
            if max_retry == 10:
                self.logger.info(
                    "Power state, max retried reached, "
                    "no pending reboot states."
                )
                break

            # get reboot reboot pending tasks
            scheduled_jobs = self.sync_invoke(
                ApiRequestType.Jobs, "jobs_sources_query",
                reboot_pending=True,
                job_type=CliJobTypes.RebootNoForce.value,
                job_ids=True
            )
            if scheduled_jobs.error is not None:
                return scheduled_jobs

            if len(scheduled_jobs.data) == 0:
                time.sleep(sleep_time)

            try:
                for job in scheduled_jobs.data:
                    # reboot and wait for completion.
                    self.logger.info(f"Reboot pending job created: task id {job}")
                    task_state = self.fetch_task(job)
                    _reboot -= 1
            except MissingResource as mr:
                self.logger.error(str(mr))
                time.sleep(sleep_time)
            except RedfishException as re:
                self.logger.error(str(re))
                time.sleep(sleep_time)

            self.logger.info(f"Sleeping {sleep_time} sec "
                             f"and waiting for reboot pending")
            time.sleep(sleep_time)
            retry_counter += 1

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
                do_wait: Optional[bool] = False,
                sleep_time: Optional[int] = 10,
                max_retry: Optional[int] = 10,
                **kwargs
                ) -> CommandResult:
        """
        :param do_wait: wait indicate to wait and confirm a action.
        :param do_async: will issue asyncio request and won't block
        :param reset_type: "On, ForceOff, ForceRestart, GracefulShutdown, PushPowerButton, Nmi"
        :param power_state: On, null
        :param boot_source_override: "None, Pxe, Floppy,
                                      Cd, Hdd, BiosSetup, Utilities,
                                      UefiTarget, SDCard, UefiHttp"
        :param boot_source_override_enabled: "Once, Continuous, Disabled"
        :param boot_source_override_mode: UEFI, Legacy
        :param sleep_time wait for job to start
        :param max_retry maximum retry.  by default reboot task will wait task to finish.
        :param interface_type: TCM1_0, TPM2_0, TPM1_
        :param filename:
        :param data_type:
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        system_state = self.sync_invoke(
            ApiRequestType.SystemQuery, "system_query"
        )

        system_actions = system_state.data['Actions']
        allowed_reset_types = []

        target = f"{self.idrac_manage_servers}{IDRAC_API.COMPUTE_RESET}"

        if '#ComputerSystem.Reset' in system_actions:
            ra = system_actions[
                '#ComputerSystem.Reset'
            ]
            allowed_reset_types = ra[
                'ResetType@Redfish.AllowableValues'
            ]
            if 'target' in ra:
                target = ra['target']

        if reset_type not in allowed_reset_types:
            raise InvalidArgument(
                f"Invalid reset type {reset_type}, "
                f"supported reset types {allowed_reset_types}")

        payload = {
            'ResetType': reset_type
        }

        self.logger.info(f"issuing reset request {payload}")

        cmd_result, api_resp = self.base_post(target, payload=payload, expected_status=202)
        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            self.logger.info(f"received task id {task_id}, fetch task state")
            task_state = self.fetch_task(task_id)
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = task_id

        if do_wait:
            self.wait_for_reboot(sleep_time, max_retry)

        return cmd_result
