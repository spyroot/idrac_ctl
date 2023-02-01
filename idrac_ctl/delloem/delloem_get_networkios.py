"""iDRAC Redfish API with Dell OEM extension
to get network ISO attach status.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class GetNetworkIsoAttachStatus(IDracManager,
                                scm_type=ApiRequestType.GetNetworkIsoAttachStatus,
                                name='net_ios_attach_status',
                                metaclass=Singleton):
    """A command query job_service_query.
    """

    def __init__(self, *args, **kwargs):
        super(GetNetworkIsoAttachStatus, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_reboot=True)
        help_text = "command get network iso status"
        return cmd_parser, "oem-net-ios-status", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                do_reboot: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes dell oem get attach status action.

        Return if drivers attached and ISO attached.

        {
        "DriversAttachStatus": "NotAttached",
        "ISOAttachStatus": "NotAttached"
        }
        python idrac_ctl.py chassis
        :param do_reboot:
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        cmd_result = self.sync_invoke(ApiRequestType.DellOemActions, "dell_oem_actions")
        redfish_action = cmd_result.discovered['GetNetworkISOImageConnectionInfo']
        target_api = redfish_action.target

        api_result = self.base_post(target_api, do_async=do_async)
        result = {}
        resp_keys = ["HostAttachedStatus",
                     "HostBootedFromISO",
                     "IPAddr", "ISOConnectionStatus",
                     "ImageName", "ShareName", "UserName"]

        if api_result is not None and api_result.extra is not None:
            data = api_result.extra.json()
            for rk in resp_keys:
                if rk in data:
                    result[rk] = data[rk]

        if do_reboot:
            cmd_reboot = self.reboot()
            if 'Status' in cmd_reboot:
                result.update({"Reboot": cmd_reboot['Status']})

        return CommandResult(result, None, None)
