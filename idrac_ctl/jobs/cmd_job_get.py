"""iDRAC fetch job from iDRAC

Command provides the option to retrieve job information  from iDRAC
and serialize back as caller as JSON, YAML, and XML.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio

from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult, save_if_needed


class JobGet(IDracManager,
             scm_type=ApiRequestType.JobGet,
             name='job_query',
             metaclass=Singleton):
    """Command gets a job from iDRAC
    """

    def __init__(self, *args, **kwargs):
        super(JobGet, self).__init__(*args, **kwargs)

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
            required=False, dest="do_async", default=False,
            help="Will create a task and will not wait."
        )

        cmd_parser.add_argument(
            '-j', '--job_id',
            required=True, dest="job_id", type=str, default=None,
            help="Job id. Example JID_744718373591"
        )

        cmd_parser.add_argument(
            '-f', '--filename',
            required=False, type=str, default="",
            help="filename if we need to save a respond to a file."
        )

        help_text = "command fetch a job"
        return cmd_parser, "job", help_text

    def execute(self, job_id: str,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query information for particular job.

        python idrac_ctl.py job --job_id JID_744718373591

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

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Managers/iDRAC.Embedded.1/" \
            f"Oem/Dell/Jobs/{job_id}?$expand=*($levels=1)"

        if not do_async:
            response = self.api_get_call(r, headers)
            self.default_error_handler(response)
        else:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))
        data = response.json()

        save_if_needed(filename, data)
        return CommandResult(data, None, None)
