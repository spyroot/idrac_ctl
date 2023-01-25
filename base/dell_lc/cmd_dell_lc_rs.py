"""iDRAC dell lc rs status

Author Mus spyroot@gmail.com
"""
import json
from abc import abstractmethod
from typing import Optional

from base import CommandResult
from base import IDracManager, ApiRequestType, Singleton


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
                uri_path: Optional[str] = None,
                remote_username: Optional[str] = None,
                remote_password: Optional[str] = None,
                device_id: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute remote service api status
        :param device_id: virtual media device id 1 or 1
        :param remote_username:  username for remote authentication
        :param remote_password:  password for remote authentication
        :param uri_path: URI path to image file.
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param data_type:  json, xml etc.
        :return: named tuple CommandResult
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target_api = "/redfish/v1/Dell/Managers/iDRAC.Embedded.1/" \
                     "DellLCService/Actions/DellLCService.GetRSStatus"
        r = f"https://{self.idrac_ip}{target_api}"

        response = self.api_post_call(r, json.dumps({}), headers)
        ok = self.default_post_success(self, response, expected=204)
        return CommandResult(response.json(), None, None)
