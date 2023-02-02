"""iDRAC virtual media eject command

Command provides the option to insert virtual disk with ISO image.
For example late we can set boot from virtual medial,
set one shot boot via one_shot cmd and reboot a host.

Example.  Retrieve list of current boot
python idrac_ctl.py current_boot

Note BootSourceOverrideEnabled and BootSourceOverrideTarget empty.

{
    "BootOptions": {
        "@odata.id": "/redfish/v1/Systems/System.Embedded.1/BootOptions"
    },
    "BootOrder": [
        "HardDisk.List.1-1",
        "NIC.Integrated.1-1-1",
        "NIC.Slot.8-1",
        "NIC.Slot.8-1",
        "NIC.Slot.8-1",
        "NIC.Slot.8-1",
        "Optical.iDRACVirtual.1-1"
    ],
    "BootOrder@odata.count": 7,
    "BootSourceOverrideEnabled": "Disabled",
    "BootSourceOverrideMode": "Legacy",
    "BootSourceOverrideTarget": "None",
    "BootSourceOverrideTarget@Redfish.AllowableValues": [
        "None",
        "Pxe",
        "Floppy",
        "Cd",
        "Hdd",
        "BiosSetup",
        "Utilities",
        "UefiTarget",
        "SDCard",
        "UefiHttp"
    ],
    "Certificates": {
        "@odata.id": "/redfish/v1/Systems/System.Embedded.1/Boot/Certificates"
    },
    "UefiTargetBootSourceOverride": null
}

python idrac_ctl.py get_virtual_media

We note that Image is null and not inserted.

"ConnectedVia": "NotConnected",
            "Description": "iDRAC Virtual Media Instance",
            "Id": "1",
            "Image": null,
            "ImageName": null,
            "Inserted": false,
            "MediaTypes": [
                "CD",
                "DVD",
                "USBStick"
            ],
            "MediaTypes@odata.count": 3,
            "Name": "VirtualMedia Instance 1",
            "Password": null,
            "TransferMethod": null,
            "TransferProtocolType": null,
            "UserName": null,
            "WriteProtected": true

Insert virtual media
python idrac_ctl.py insert_virtual_media --uri_path http://my_ip/ubuntu-22.04.1-desktop-amd64.iso --device_id 1

Author Mus spyroot@gmail.com
"""
import argparse
import warnings
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.cmd_exceptions import InvalidArgument


class VirtualMediaInsert(IDracManager,
                         scm_type=ApiRequestType.VirtualMediaInsert,
                         name='virtual_disk_insert',
                         metaclass=Singleton):
    """iDRACs cmd insert virtual media
    Virtual medial must be empty, otherwise command will throw exception.
    Called must first eject existing virtual media.
    """

    def __init__(self, *args, **kwargs):
        super(VirtualMediaInsert, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--remote_username', required=False, type=str,
                             default=None,
                             help="remote username for authentication if required")

        cmd_arg.add_argument('--remote_password', required=False, type=str,
                             default=None,
                             help="remote password for authentication if required")

        cmd_arg.add_argument('--uri_path', required=False, type=str,
                             default=None,
                             help="url path to iso file. Example http://1.1.1.1/test.iso")

        cmd_arg.add_argument('--device_id', required=False, type=str,
                             default="1",
                             help="Default device id. Example 1 or 2")

        help_text = "command insert virtual media"
        return cmd_arg, "insert_vm", help_text

    def execute(self,
                uri_path: Optional[str] = None,
                remote_username: Optional[str] = None,
                remote_password: Optional[str] = None,
                device_id: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute command, inserts a virtual media eject.
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

        new_api = False
        virtual_media = self.sync_invoke(
            ApiRequestType.VirtualMediaGet,
            "virtual_disk_query"
        )
        if self.version_api():
            new_api = True
            # this for a future issue if old API doesn't work

        if new_api is False:
            warnings.warn("Detected old rest API.")

        members = virtual_media.data['Members']
        actions = [self.discover_redfish_actions(self, m) for m
                   in members if m['Id'] == device_id]

        if len(actions) == 0:
            dev_id = [m['Id'] for m in members]
            raise InvalidArgument(f"Invalid device id {device_id}, "
                                  f"support device id {dev_id}")

        # if another image already mounted.
        inserted = {'image': m['Image'] for
                    m in members if m['Id'] == device_id and m['Inserted']}

        if 'image' in inserted:
            raise InvalidArgument(f"Image {inserted['image']} "
                                  f"already inserted. Eject media first.")

        target = [a['InsertMedia'].target for a in actions][-1]
        # r = f"https://{self.idrac_ip}{target}"

        payload = {
            'Image': uri_path,
            'Inserted': True,
            'WriteProtected': True,
            'UserName': remote_username,
            'Password': remote_password,
        }

        for key, value in dict(payload).items():
            if value is None:
                del payload[key]

        api_result = self.base_post(
            target, payload=payload, do_async=do_async,
            expected_status=204, verbose=verbose
        )

        if api_result.data['Status']:
            resp = self.parse_task_id(api_result)
            api_result.data.update(resp)

        # response = self.api_post_call(r, json.dumps(payload), headers)
        # ok = self.default_post_success(self, response, expected=204)
        return api_result
