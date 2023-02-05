"""iDRAC query jobs services

Command  query jobs services.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class JobServices(IDracManager,
                  scm_type=ApiRequestType.JobServices,
                  name='job_service_query',
                  metaclass=Singleton):
    """A command query job_service_query.
    """

    def __init__(self, *args, **kwargs):
        super(JobServices, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command query jobs services"
        return cmd_parser, "jobs-service", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes query job services.
        python idrac_ctl.py query
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = "/redfish/v1/JobService"
        cmd_result = self.base_query(target_api,
                                     filename=filename,
                                     do_async=do_async,
                                     do_expanded=do_expanded)

        return CommandResult(cmd_result, None, None)
