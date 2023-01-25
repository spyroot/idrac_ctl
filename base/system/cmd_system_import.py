"""iDRAC firmware command

Command provides the option to import configuration.
python idrac_ctl.py system-import --config system.json

Author Mus spyroot@gmail.com
"""
import argparse
import json
from abc import abstractmethod
from typing import Optional

from base import CommandResult, UnexpectedResponse
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

        help_text = "command import system configuration"
        return cmd_arg, "system-import", help_text

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
        ok = self.default_post_success(self, response, expected=202)
        resp_hdr = response.headers
        if 'Location' not in resp_hdr:
            raise UnexpectedResponse("rest api failed.")

        location = response.headers['Location']
        job_id = location.split("/")[-1]

        if not do_async:
            data = self.fetch_job(job_id)
        else:
            data = {"job_id": job_id}

        return CommandResult(data, None, None)
