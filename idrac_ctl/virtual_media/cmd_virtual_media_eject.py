"""iDRAC virtual media eject command

Command provides the option to eject  virtual disk from iDRAC.

Example:
    python idrac_ctl.py eject_virtual_media --device_id 1

Will eject virtual device id 1

Author Mus spyroot@gmail.com
"""
import argparse
import json
import warnings
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult, InvalidArgument
from idrac_ctl import IDracManager, ApiRequestType, Singleton


class VirtualMediaEject(IDracManager,
                        scm_type=ApiRequestType.VirtualMediaEject,
                        name='virtual_disk_eject',
                        metaclass=Singleton):
    """iDRACs cmd ejects virtual media
    Virtual medial must be inserted, otherwise command throw exception.
    """
    def __init__(self, *args, **kwargs):
        super(VirtualMediaEject, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)
        cmd_arg.add_argument('--device_id', required=False, type=str,
                             default="1",
                             help="virtual media device id. Example 1 or 2")

        help_text = "command eject the virtual media"
        return cmd_arg, "eject_vm", help_text

    def execute(self,
                device_id: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Execute command virtual media eject.

        :param device_id: virtual media device id. (1 or 2)
        :param verbose: enables verbose output
        :param do_async: will not block and return result as future.
        :param data_type:  json, xml etc.
        :return: named tuple CommandResult
        :raise: InvalidArgument if media already ejected or invalid device id
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

        if new_api is False:
            warnings.warn("Old api")

        members = virtual_media.data['Members']
        actions = [self.discover_redfish_actions(self, m) for m
                   in members if m['Id'] == device_id]
        if len(actions) == 0:
            valid_dev_id = [m['Id'] for m in members]
            raise InvalidArgument(f"Invalid device id {device_id}, "
                                  f"supported device id {valid_dev_id}")

        # if another image already mounted.
        inserted = {'image': m['Image'] for
                    m in members if m['Id'] == device_id
                    and m['Inserted'] is False}

        if 'image' in inserted:
            raise InvalidArgument(f"Image already ejected")

        eject_rest = [a['EjectMedia'].target for a in actions][-1]
        r = f"https://{self.idrac_ip}{eject_rest}"

        api_result = {}
        payload = {}
        response = self.api_post_call(r, json.dumps(payload), headers)
        if self.default_post_success(self, response):
            api_result = self.api_success_msg(True)

        return CommandResult(api_result, None, None)
