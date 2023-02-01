"""iDRAC enable boot options.

This cmd return Dell Boot Sources Configuration and the related
resources for particular device

Example.
python idrac_ctl.py boot-source-get --dev NIC.Slot.8-1


Author Mus spyroot@gmail.com
"""
import argparse
import asyncio

from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult, save_if_needed


class EnableBootOptions(IDracManager,
                        scm_type=ApiRequestType.EnableBootOptions,
                        name='boot_source_query',
                        metaclass=Singleton):
    """
    Command fetch boot option for particular device.
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
                                             description="command fetch the boot source for device/devices")
        # idrac_ctl.py boot-source-get --dev NIC.Slot.8-1
        cmd_parser.add_argument('--async', action='store_true', required=False,
                                dest="do_async", default=False,
                                help="will use async task and will not wait")

        cmd_parser.add_argument('--dev', required=False, dest="boot_source",
                                type=str, default=None,  metavar="DEVICE",
                                help="fetch verbose information for a device. Example --dev NIC.Slot.8-1")

        cmd_parser.add_argument('-f', '--filename', required=False,
                                type=str, default="",
                                help="filename if we need to save a respond to a file.")

        help_text = "command fetch the boot source for device/devices"
        return cmd_parser, "boot-source-get", help_text

    def execute(self,
                boot_source: Optional[str] = None,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query information for particular boot source device from idrac.
        Example python idrac_ctl.py get_boot_source --dev "HardDisk.List.1-1"
        :param boot_source: a device HardDisk.List.1-1
        :param do_async: note async will subscribe to an event loop.
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"boot_source:{boot_source} do_async:{do_async} filename:{filename}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        result = self.sync_invoke(ApiRequestType.BootOptions, "boot_sources_query")
        boot_data_sources = {}
        for full_dev_path in result.data:
            r = f"https://{self.idrac_ip}{full_dev_path}?$expand=*($levels=1)"
            if not do_async:
                response = self.api_get_call(r, headers)
                self.default_error_handler(response)
            else:
                loop = asyncio.get_event_loop()
                response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))

            dev_data = response.json()
            devs = full_dev_path.split("/")
            if len(devs) > 0:
                dev = devs[-1]
                # add all by default
                if boot_source is None:
                    boot_data_sources[dev] = dev_data
                elif boot_source is not None and boot_source.lower() in dev.lower():
                    boot_data_sources[dev] = dev_data
                    break

        save_if_needed(filename, boot_data_sources)
        return CommandResult(boot_data_sources, None, None)
