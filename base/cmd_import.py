"""iDRAC firmware command

Command provides the option to retrieve firmware setting from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command caller can save
to a file and consume asynchronously or synchronously.

Author Mus spyroot@gmail.com
"""
import argparse
import json
from abc import abstractmethod
from typing import Optional

from base import CommandResult
from base import IDracManager, ApiRequestType, Singleton


class ImportSystemConfig(IDracManager, scm_type=ApiRequestType.ImportSystem,
                         name='import_sysconfig',
                         metaclass=Singleton):
    """
    Command implementation import system configuration.
    """

    def __init__(self, *args, **kwargs):
        super(ImportSystemConfig, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """

        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument('--config', required=True, dest="config", type=str,
                             default=None, help="Import system config")

        cmd_arg.add_argument('--async', action='store_true', required=False, dest="do_async",
                             default=False, help="Will do async request.")

        cmd_arg.add_argument('--deep', action='store_true', required=False, dest="do_deep",
                             default=False, help="deep view to each pci.")

        cmd_arg.add_argument('-f', '--filename',
                             required=False, type=str, default="",
                             help="filename, if we need save to a file.")

        help_text = "fetch the firmware view"
        return cmd_arg, "import", help_text

    def execute(self,
                config: str,
                shutdown_type: Optional[str] = "Graceful",
                host_power_state: Optional[str] = "Off",
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                do_deep: Optional[bool] = False,
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Query firmware from idrac

        ImportBuffer
        Buffer content to perform import. Required only for LOCAL
        and not required for CIFS, NFS, HTTP, or HTTPS.

        ShutdownType ShutdownType Graceful, Forced, NoReboot

        HostPowerState  On, Off

        TimeToWait The time to wait for the host to shut down. Default and
        minimum value is 300 seconds. Maximum value is 3600
        seconds.

        Share parameters and values
        IPAddress IP address of the network share
        ShareName Name of network share
        File name for the SCP
        LOCAL, CIFS, NFS, HTTP, HTTPS


        ExportFormat
        ExportUse
        IncludeInExport
        ShareParameters

        :param shutdown_type:
        :param host_power_state:
        :param config:
        :param shutdown_type:
        :param do_deep: will return verbose output for each pci device.
        :param do_async: will schedule asyncio task.
        :param verbose: verbose output.
        :param filename: if filename indicate call will save respond to a file.
        :param data_type: a data serialized back.
        :return: in data type json will return json
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"do_deep:{do_deep} do_async:{do_async} filename:{filename}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        open_file = open(config, "r")
        modify_file = open_file.read()
        modify_file = modify_file.replace('\n', "")
        modify_file = modify_file.replace("   ", "")
        open_file.close()

        payload = {"ShutdownType": shutdown_type.title(),
                   "HostPowerState": host_power_state.title(),
                   "ImportBuffer": modify_file,
                   "ShareParameters": {"Target": "ALL"}
                   }

        r = f"https://{self.idrac_ip}/redfish/v1/Managers/iDRAC.Embedded.1/" \
            f"Actions/Oem/EID_674_Manager.ImportSystemConfiguration"

        response = self.api_post_call(r, json.dumps(payload), headers)
        data = response.json()
        print(response.headers)
        print(data)

        self.default_post_success(self, response)
        job_id = response.headers['Location'].split("/")[-1]

        #
        # if not do_async:
        #     response = self.api_get_call(r, headers)
        #     self.default_error_handler(response)
        # else:
        #     loop = asyncio.get_event_loop()
        #     response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))
        #
        # self.default_error_handler(response)
        # data = response.json()
        #
        # save_if_needed(filename, data)
        return CommandResult({}, None, None)
