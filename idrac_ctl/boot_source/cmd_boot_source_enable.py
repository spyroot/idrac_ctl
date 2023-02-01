"""iDRAC enable boot options.

Command provides the option to enable boot source,
so it is used during a boot process.

For example.
python idrac_ctl.py boot-source-enable --dev NIC.Slot.8-1 --enable yes

Example
idrac_ctl.py set_boot_source --dev NIC.Slot.8-1 --enable yes

Enables boot on nic slot 8-1

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult
from idrac_ctl.cmd_utils import str2bool
from idrac_ctl.idrac_manager import PatchRequestFailed


class EnableBootOptions(IDracManager,
                        scm_type=ApiRequestType.EnableBootOptions,
                        name='boot_patch',
                        metaclass=Singleton):
    """
    Command enable boot option
    """

    def __init__(self, *args, **kwargs):
        super(EnableBootOptions, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False,
                                             description="command enable as boot source a device.")

        cmd_parser.add_argument('--async', action='store_true', required=False, dest="do_async",
                                default=False,
                                help="Will create a task and will not wait.")

        cmd_parser.add_argument('-f', '--filename', required=False, type=str,
                                default="",
                                help="filename if we need to save a respond to a file.")

        cmd_parser.add_argument('--dev', required=True, dest="boot_source",
                                type=str, default=None, metavar="DEVICE",
                                help="fetch verbose information for a device. Example --dev NIC.Slot.8-1")

        cmd_parser.add_argument('--enable', required=True, metavar="yes",
                                dest="is_enabled", type=str2bool, nargs='?',
                                help="Enable or Disable target boot device. yes|no, true|false")

        help_text = "command enable the boot on a particular device."
        return cmd_parser, "boot-source-enable", help_text

    def execute(self,
                boot_source: str,
                is_enabled: bool,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query boot source from idrac
        :param is_enabled:  Enable or disable target boot device.
        :param boot_source: A device  Example, HardDisk.List.1-1 , NIC.Slot.8-1 etc
        :param do_async:
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"boot_source:{boot_source}  is_enabled:{is_enabled}, "
                  f"do_async:{do_async} filename:{filename}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        if boot_source is None:
            raise ValueError("Please indicate boot source.")

        dev_result = self.sync_invoke(ApiRequestType.BootOptions, "boot_sources_query")
        target_dev = None
        boot_data_sources = []
        for full_dev_path in dev_result.data:
            devs = full_dev_path.split("/")
            if len(devs) > 0:
                dev = devs[-1]
                boot_data_sources.append(dev)
                if boot_source.lower() in dev.lower():
                    target_dev = full_dev_path
                    break

        if target_dev is None:
            print(f"Unknown dev. available boot source. {boot_data_sources}")
            return CommandResult(None, None, None)

        ok = False
        json_data = {}
        try:
            r = f"https://{self.idrac_ip}{target_dev}"
            payload = {"BootOptionEnabled": bool(is_enabled)}
            if not do_async:
                resp = self.api_patch_call(r, json.dumps(payload), hdr=headers)
                ok = self.default_patch_success(self, resp)
            else:
                loop = asyncio.get_event_loop()
                ok, resp = loop.run_until_complete(
                        self.api_async_patch_until_complete(
                                r, json.dumps(payload), headers)
                )

                json_data = resp.json()
                if '@Message.ExtendedInfo' in json_data:
                    json_data = json_data['@Message.ExtendedInfo']

        except PatchRequestFailed as patch_err:
            print("Error:", patch_err)
            pass
        except Exception as err:
            print("Error:", err)
            pass

        api_result = {"Status": ok}
        api_result.update(json_data)
        return CommandResult(api_result, None, None)
