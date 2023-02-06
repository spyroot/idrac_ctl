"""iDRAC query chassis services

Command provide option to trigger and apply current pending jobs.
Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl.cmd_exceptions import UnexpectedResponse
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult
from idrac_ctl.shared import JobTypes


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
            print(f"Applying job {job}")
            self.logger.info(f"Rebooting a host to apply pending job {job}")
            self.reboot(do_watch=True)
            data = self.fetch_job(job, wait_completion=True)
            self.default_json_printer(data)

        cmd_result = self.base_post(target_api, pd, do_async=do_async)
        if cmd_result.error is not None:
            return cmd_result

        job_id = ""
        try:
            if cmd_result.data is not None and cmd_result.data['Status']:
                job_id = self.parse_task_id(cmd_result)
                self.logger.info(f"job id", {job_id})
                if do_watch:
                    # if we need watch for a job, we first reboot and watch and wait.
                    if do_reboot:
                        self.reboot(do_watch)
                    cmd_result.data = self.fetch_job(job_id)
        except UnexpectedResponse as un:
            cmd_result.data = {
                "Status": False,
                "Error": str(un)
            }
            self.logger.error(un)

        return CommandResult(cmd_result.data, None, {"job_id": job_id}, None)
