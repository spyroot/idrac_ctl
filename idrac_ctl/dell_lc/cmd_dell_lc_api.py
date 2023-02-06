"""iDRAC cmd fetch dell lc api status.
Author Mus spyroot@gmail.com
"""
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton


class GetRemoteServicesAPIStatus(IDracManager,
                                 scm_type=ApiRequestType.RemoteServicesAPIStatus,
                                 name='dell_lc_status',
                                 metaclass=Singleton):
    """iDRACs fetch Dell LC status
    """
    def __init__(self, *args, **kwargs):
        super(GetRemoteServicesAPIStatus, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = cls.base_parser()
        help_text = "command fetch service api status"
        return cmd_arg, "service-api-status", help_text

    def execute(self,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute command and fetch service api status.
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param data_type:  json, xml etc.
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target_api = "/redfish/v1/Dell/Managers/iDRAC.Embedded.1/DellLCService/" \
                     "Actions/DellLCService.GetRemoteServicesAPIStatus"
        r = f"https://{self.idrac_ip}{target_api}"
        response = self.api_post_call(r, json.dumps({}), headers)
        _ = self.default_post_success(self, response, expected=204)
        return CommandResult(response.json(), None, None, None)
