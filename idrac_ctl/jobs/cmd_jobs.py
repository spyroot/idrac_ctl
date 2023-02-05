"""iDRAC list of jobs.
 source from iDRAC
Command provides the option to retrieve list of jobs and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command
caller can save to a file and consume asynchronously or synchronously.

Example.

List of scheduled jobs

idrac_ctl.py jobs --scheduled

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional
from datetime import datetime
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class JobList(IDracManager,
              scm_type=ApiRequestType.Jobs,
              name='jobs_sources_query',
              metaclass=Singleton):
    """Command handler for list of jobs
    """

    def __init__(self, *args, **kwargs):
        super(JobList, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument(
            '--async', action='store_true',
            required=False, dest="do_async",
            default=False,
            help="Will create a task and will not wait."
        )

        cmd_parser.add_argument(
            '-e', '--expanded', action='store_true',
            required=False, dest="do_expanded",
            default=False,
            help="expanded request for deeper view."
        )

        cmd_parser.add_argument(
            '-f', '--filename', required=False, type=str,
            default="",
            help="filename if we need to save a respond to a file."
        )

        cmd_parser.add_argument(
            '--scheduled', action='store_true',
            required=False, dest="filter_scheduled",
            default=False,
            help="return only scheduled."
        )

        cmd_parser.add_argument(
            '--completed', action='store_true',
            required=False, dest="filter_completed",
            default=False,
            help="return only completed."
        )

        cmd_parser.add_argument(
            '--reboot_completed', action='store_true',
            required=False, dest="reboot_completed",
            default=False,
            help="returns only completed after reboot."
        )

        cmd_parser.add_argument(
            '--running', action='store_true',
            required=False, dest="running",
            default=False,
            help="returns only completed after reboot."
        )

        cmd_parser.add_argument(
            '--reboot_pending', action='store_true',
            required=False, dest="reboot_pending",
            default=False,
            help="returns only reboot pending jobs."
        )

        cmd_parser.add_argument(
            '--failed', action='store_true',
            required=False, dest="failed",
            default=False,
            help="returns only failed jobs."
        )

        cmd_parser.add_argument(
            '--sort_by_time', action='store_true',
            required=False, dest="sort_by_time",
            default=True,
            help="Sort jobs by time. First entry the last job."
        )

        cmd_parser.add_argument(
            '--job_type',  required=False,
            default="", type=str,
            help="filter by job type. (Example bios_config, firmware_update)"
        )

        # RebootCompleted
        help_text = "command fetch a list of jobs"
        return cmd_parser, "jobs", help_text

    @staticmethod
    def resolve_job_type(jb_type: str):
        """

        """
        if jb_type == "bios_config":
            return "BIOSConfiguration"
        elif jb_type == "firmware_update":
            return "BIOSConfiguration"
        elif jb_type == "reboot_no_force":
            return "RebootNoForce"
        else:
            ValueError("Unknown job type")

    def execute(self,
                filename: [str] = None,
                filter_scheduled: Optional[bool] = False,
                filter_completed: Optional[bool] = False,
                reboot_completed: Optional[bool] = False,
                reboot_pending: Optional[bool] = False,
                failed: Optional[bool] = False,
                running: Optional[bool] = False,
                sort_by_time: Optional[bool] = True,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                job_type: Optional[str] = "",
                **kwargs) -> CommandResult:
        """Command return list idrac jobs

        :param failed: retrieve failed jobs
        :param sort_by_time:  sort by start time
        :param reboot_pending: retrieve jobs reboot pending status
        :param running: retrieve running jobs
        :param reboot_completed: retrieve completed jobs
        :param filter_scheduled: retrieve scheduled jobs
        :param filter_completed:  retrieve completed
        :param do_async: make async request.
        :param verbose: enable verbose
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :param do_expanded: returns expanded result for API call
        :param job_type: filter on job_type
        :return: CommandResult and if filename provide will save to a file.
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/" \
            f"Managers/iDRAC.Embedded.1/Jobs?$expand=*($levels=1)"

        response = self.api_get_call(r, headers)
        data = response.json()
        self.default_error_handler(response)
        filtered_data = []
        if filter_scheduled:
            scheduled_jobs = [job for job in data['Members'] if job['JobState'] == 'Scheduled'
                              or job['JobState'] == 'Scheduling']
            filtered_data += scheduled_jobs
        if filter_completed:
            completed_jobs = [job for job in data['Members'] if job['JobState'] == 'Completed']
            filtered_data += completed_jobs
        if reboot_completed:
            reboot_completed_jobs = [job for job in data['Members'] if job['JobState'] == 'RebootCompleted']
            filtered_data += reboot_completed_jobs
        if running:
            reboot_completed_jobs = [job for job in data['Members'] if job['JobState'] == 'Running']
            filtered_data += reboot_completed_jobs
        if reboot_pending:
            reboot_pending_jobs = [job for job in data['Members'] if job['JobState'] == 'RebootPending']
            filtered_data += reboot_pending_jobs
        if failed:
            reboot_pending_jobs = [job for job in data['Members'] if job['JobState'] == 'Failed']
            filtered_data += reboot_pending_jobs
        # default
        if filter_scheduled is False and filter_completed \
                is False and reboot_completed is False and running is False and reboot_pending is False:
            filtered_data = data

        if sort_by_time:
            if isinstance(filtered_data, dict) and 'Member' in filtered_data:
                member_data = filtered_data['Members']
            elif isinstance(filtered_data, list):
                member_data = filtered_data
            else:
                member_data = [filtered_data]
            filtered_data = sorted(
                member_data, reverse=True, key=lambda
                    x: datetime.fromisoformat(x['StartTime']).timestamp()
                if 'ActualRunningStartTime' in x else None
            )
        job_type = self.resolve_job_type(job_type)

        if job_type is not None and len(job_type) > 0:
            filtered_data = [d for d in filtered_data if d['JobType'] == job_type]
            # BIOSConfiguration
        return CommandResult(filtered_data, None, None)
