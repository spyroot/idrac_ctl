"""iDRAC fetch dell lc rs status
Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.idrac_shared import IdracApiRespond, IDRAC_API


class GetRemoteRssAPIStatus(IDracManager,
                            scm_type=ApiRequestType.RemoteServicesRssAPIStatus,
                            name='dell_lc_rs_status',
                            metaclass=Singleton):
    """iDRACs cmd get status remote services api
    """

    def __init__(self, *args, **kwargs):
        super(GetRemoteRssAPIStatus, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = cls.base_parser()
        help_text = "command fetch service api status"
        return cmd_arg, "service-api-rs-status", help_text

    def execute(self,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute remote service rs api status.
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param data_type:  json, xml etc.
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target_api = f"{self.idrac_members}/{IDRAC_API.DellLCService}" \
                     f"/Actions/DellLCService.GetRSStatus"
        cmd_result, api_resp = self.base_post(target_api, payload={})

        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            task_state = self.fetch_task(task_id)
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = task_id

        return cmd_result
