"""iDRAC query jobs services

Command  query jobs services.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class JobRmDellServices(IDracManager,
                        scm_type=ApiRequestType.JobRmDellServices,
                        name='job_delete_all',
                        metaclass=Singleton):
    """A command query job_service_query.
    """

    def __init__(self, *args, **kwargs):
        super(JobRmDellServices, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command delete all jobs"
        return cmd_parser, "job-rm-all", help_text

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
        target_api = "/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellJobService"
        cmd_result = self.base_query(target_api,
                                     filename=filename,
                                     do_async=do_async,
                                     do_expanded=do_expanded)
        actions = self.discover_redfish_actions(self, cmd_result.data)
        payload = {'JobID': "JID_CLEARALL_FORCE"}
        target_api = actions['DeleteJobQueue'].target
        api_result = self.base_post(target_api, do_async=do_async,
                                    payload=payload, expected_status=200)
        result = {}
        if api_result is not None and api_result.extra is not None:
            data = api_result.extra.json()
            result.update(data)

        return CommandResult(result, None, None)
