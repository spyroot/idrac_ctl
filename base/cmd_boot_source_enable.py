"""iDRAC enable boot options.

Command provides the option to retrieve boot source from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command
caller can save to a file and consume asynchronously or synchronously.

Doc
https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v3.3-series/
idrac9_3.36_redfishapiguide/dellbootsources?guid=guid-4803ff0e-76ad-42c5-a971-820123cd0b83&lang=en-us

Example
idrac_ctl.py set_boot_source --dev NIC.Slot.8-1 --enable yes

Enables boot on nic slot 8-1

Author Mus spyroot@gmail.com
"""
import argparse
import json
from abc import abstractmethod
from typing import Optional

from base import Singleton, ApiRequestType, IDracManager, CommandResult
from base.cmd_utils import str2bool
from base.idrac_manager import PatchFailed


class EnableBootOptions(IDracManager, scm_type=ApiRequestType.EnableBootOptions,
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
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument('--async', action='store_true', required=False, dest="do_async",
                                default=False,
                                help="Will create a task and will not wait.")

        cmd_parser.add_argument('-f', '--filename', required=False, type=str,
                                default="",
                                help="filename if we need to save a respond to a file.")

        cmd_parser.add_argument('--dev', required=True, dest="boot_source", type=str,
                                default=None,
                                help="Fetch verbose information for a boot device.")

        cmd_parser.add_argument('--enable', required=True,
                                dest="is_enabled", type=str2bool, nargs='?',
                                help="Enable or Disable target boot device. yes|no, true|false")

        help_text = "Fetch the boot source"
        return cmd_parser, "set_boot_source", help_text

    def execute(self, boot_source: str,
                is_enabled: bool,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False, **kwargs) -> CommandResult:
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

        cmd_result = CommandResult(None, None, None)

        try:
            r = f"https://{self.idrac_ip}{target_dev}"
            payload = {"BootOptionEnabled": bool(is_enabled)}
            resp = self.api_patch_call(r, json.dumps(payload), hdr=headers)
            self.default_json_printer(self, resp.json())
            self.default_patch_success(self, resp)
            cmd_result.data = CommandResult(resp.json(), None, None)
        except PatchFailed as patch_err:
            print("Error:", patch_err)
            pass
        except Exception as err:
            print("Error:", err)
            pass

        self.default_json_printer(self, cmd_result.data)

        return cmd_result
