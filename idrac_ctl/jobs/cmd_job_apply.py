"""iDRAC query chassis services

Command provide option to trigger and apply current pending jobs.
Author Mus spyroot@gmail.com
"""
import logging
from abc import abstractmethod
from typing import Optional

from idrac_ctl.redfish_manager import CommandResult
from idrac_ctl.idrac_manager import IDracManager
from idrac_ctl.idrac_shared import Singleton, ApiRequestType
from idrac_ctl.idrac_shared import JobTypes, IdracApiRespond


class JobApply(IDracManager,
               scm_type=ApiRequestType.JobApply,
               name='job_apply',
               metaclass=Singleton):
    """A command query job_service_query.
    """
    def __init__(self, *args, **kwargs):
        super(JobApply, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_reboot=True)
        cmd_parser.add_argument(
            'setting', choices=['bios', 'attribute', 'raid'],
            default="bios",
            help="what setting we apply a change. (bios, raid, etc)"
        )
        cmd_parser.add_argument(
            '-w', '--watch', action='store_true',
            required=False, dest="do_watch",
            default=False,
            help="Will block and wait a job to complete. note if job require reboot, "
                 "pass -r or --reboot, otherwise job will not start."
        )

        help_text = "command apply current pending jobs"
        return cmd_parser, "job-apply", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                setting: Optional[str] = "bios",
                do_watch: Optional[bool] = False,
                do_reboot: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes apply job and trigger execution.
        :param do_async: note async will subscribe to an event loop.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param setting: job we apply
        :param do_watch: will watch job progress.
        :param do_reboot: many jobs applied only after boot, watch will just block.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = "/redfish/v1/Managers/iDRAC.Embedded.1/Jobs"
        bios = "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"

        if setting == "bios":
            pd = {
                "TargetSettingsURI": bios
            }
        else:
            pd = {}

        scheduled_jobs = self.sync_invoke(
            ApiRequestType.Jobs, "jobs_sources_query",
            filter_scheduled=True, job_type=JobTypes.BIOS_CONFIG, job_ids=True
        )

        if scheduled_jobs.error is not None:
            return scheduled_jobs

        # if we have scheduled job
        for job in scheduled_jobs.data:
            # reboot and wait for completion.
            self.logger.info(f"Rebooting a host to apply pending job {job}")
            cmd_result = self.reboot(do_watch=True)
            if cmd_result.error:
                logging.info("Failed reboot a host")
                break
            task_state = self.fetch_task(job)
            if task_state.value == task_state.Completed:
                break

        cmd_result, api_resp = self.base_post(target_api, pd, do_async=do_async)
        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            job_id = cmd_result.data['job_id']
            task_state = self.fetch_task(cmd_result.data['job_id'])
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = job_id
        else:
            if api_resp.Success or api_resp.Ok:
                return cmd_result

        return cmd_result
