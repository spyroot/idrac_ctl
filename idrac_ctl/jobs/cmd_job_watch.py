"""iDRAC delete job from iDRAC action

Command provides the option to delete a
job from iDRAC.

Author Mus spyroot@gmail.com
"""
import argparse

from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class JobWatch(IDracManager,
               scm_type=ApiRequestType.JobWatch,
               name='job_watch',
               metaclass=Singleton):
    """Command watch job progress.
    """

    def __init__(self, *args, **kwargs):
        super(JobWatch, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument(
            '--async', action='store_true', required=False, dest="do_async",
            default=False, help="Will create a task and will not wait.")

        cmd_parser.add_argument(
            '-j', '--job_id', required=True, dest="job_id", type=str,
            default=None, help="Job id. Example JID_744718373591")

        cmd_parser.add_argument(
            '-f', '--filename', required=False, type=str,
            default="",
            help="filename if we need to save a respond to a file.")

        help_text = "command watch a job"
        return cmd_parser, "job-watch", help_text

    def execute(self, job_id: str,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes delete job from iDRAC action

        python idrac_ctl.py del_job --job_id RID_744980379189

        :param job_id: iDRAC job_id JID_744718373591
        :param do_async: note async will subscribe to an event loop.
        :param verbose: enables verbose output
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"boot_source:{job_id} do_async:{do_async} filename:{filename}")
            print(f"the rest of args: {kwargs}")

        data = self.fetch_job(job_id)
        return CommandResult(data, None, None)
