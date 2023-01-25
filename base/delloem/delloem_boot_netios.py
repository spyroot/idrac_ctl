"""iDRAC Redfish API with Dell OEM extension
to boot from network ISO.

python idrac_ctl.py oem-boot-netios --ip_addr 10.241.7.99 \
--share_name sambashare --remote_image ubuntu-22.04.1-desktop-amd64.iso

python idrac_ctl.py oem-attach-status
{
    "DriversAttachStatus": "NotAttached",
    "ISOAttachStatus": "Attached"
}

Author Mus spyroot@gmail.com
"""
import json
from abc import abstractmethod
from typing import Optional
from base import Singleton, ApiRequestType, IDracManager, CommandResult


class DellOemNetIsoBoot(IDracManager,
                        scm_type=ApiRequestType.DellOemNetIsoBoot,
                        name='delloem_netios_boot',
                        metaclass=Singleton):
    """A command uses dell oem to attach ISO
    """

    def __init__(self, *args, **kwargs):
        super(DellOemNetIsoBoot, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_remote_share=True)
        help_text = "command boot from network iso "
        return cmd_parser, "oem-boot-netios", help_text

    def execute(self,
                ip_addr: Optional[str] = None,
                share_type: Optional[str] = None,
                share_name: Optional[str] = None,
                remote_image: Optional[str] = None,
                remote_username: Optional[str] = None,
                remote_password: Optional[str] = None,
                remote_workgroup: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes dell oem ConnectNetworkISOImage

        :param ip_addr: ip address of NFS or CIFS
        :param share_type: NFS|CIFS
        :param share_name: share name
        :param remote_image:  path to image
        :param remote_username: remote username if required for NFS or CIFS
        :param remote_password: remote password if required for NFS or CIFS
        :param remote_workgroup:
        :param do_async: note async will subscribe to an event loop.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        cmd_result = self.sync_invoke(ApiRequestType.DellOemActions, "dell_oem_actions")
        redfish_action = cmd_result.discovered['ConnectNetworkISOImage']
        target_api = redfish_action.target
        # args = redfish_action.args

        payload = {
            'IPAddress': ip_addr,
            'ShareType': share_type,
            'ShareName': share_name,
            'ImageName': remote_image,
            'UserName': remote_username,
            'Password': remote_password,
            'Workgroup': remote_workgroup,
        }

        for key, value in dict(payload).items():
            if value is None:
                del payload[key]

        api_result = self.base_post(target_api, payload=payload,
                                    do_async=do_async, expected_status=202)
        result = {}
        if api_result is not None and api_result.extra is not None:
            data = api_result.extra.json()
            result = data
            job_id = self.job_id_from_header(api_result.extra)
            print(api_result.extra.headers)

        return CommandResult(result, None, None)
