"""iDRAC import system config from json file.

Command provides the option to import configuration.

python idrac_ctl.py system-export --filename system.json
python idrac_ctl.py system-import --config system.json

Author Mus spyroot@gmail.com
"""
import argparse
import json
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from base import CommandResult
from base import IDracManager, ApiRequestType, Singleton
from base.cmd_exceptions import InvalidArgument


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

        cmd_arg.add_argument('-f', '--filename',
                             required=False, type=str, default="",
                             help="filename, if we need save to a file.")

        cmd_arg.add_argument('--shutdown_type',
                             required=False, type=str, default="Graceful",
                             help="Graceful, Forced, NoReboot.")

        cmd_arg.add_argument('--host_power_state',
                             required=False, type=str, default="On",
                             help="Graceful, Forced, NoReboot.")

        cmd_arg.add_argument('--time_to_wait',
                             required=False, type=int, default=300,
                             help="The time to wait for the host to shut down. "
                                  "Default and minimum value is 300 seconds. Maximum value is 3600 seconds..")

        help_text = "command import system configuration"
        return cmd_arg, "system-import", help_text

    def execute(self,
                config: str,
                shutdown_type: Optional[str] = "Graceful",
                host_power_state: Optional[str] = "Off",
                time_to_wait: Optional[str] = "",
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
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

        :param host_power_state: On, Off
        :param config: path to a config file.
        :param shutdown_type:  Graceful, Forced, NoReboot.
        :param time_to_wait:
        :param do_async: will schedule asyncio task.
        :param filename: if filename indicate call will save respond to a file.
        :param verbose: verbose output.
        :param data_type: a data serialized back.
        :return: in data type json will return json
        """
        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"shutdown_type:{shutdown_type} "
                  f"host_power_state:{host_power_state} "
                  f"do_async:{do_async} "
                  f"filename:{filename}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        shutdown_types = ['Graceful', 'Forced', 'NoReboot']
        host_power_states = ['On', 'Off']

        if shutdown_type.title() not in shutdown_type:
            raise InvalidArgument(f"Invalid shutdown type "
                                  f"{shutdown_type} supported {shutdown_types}")

        if host_power_state.title() not in host_power_states:
            raise InvalidArgument(f"Invalid power state type "
                                  f"{host_power_states} supported {host_power_states}")

        path_config = Path(config).expanduser().resolve()
        if not path_config.is_file():
            raise InvalidArgument(f"Invalid path to a config file.")

        with open(str(path_config), "r") as f:
            buf = f.read()
            buf = buf.replace('\n', "")
            buf = buf.replace("   ", "")

        payload = {"ShutdownType": shutdown_type.title(),
                   "HostPowerState": host_power_state.title(),
                   "ImportBuffer": buf,
                   "ShareParameters": {"Target": "ALL"}
                   }

        r = f"https://{self.idrac_ip}/redfish/v1/Managers/iDRAC.Embedded.1/" \
            f"Actions/Oem/EID_674_Manager.ImportSystemConfiguration"

        response = self.api_post_call(r, json.dumps(payload), headers)
        ok = self.default_post_success(self, response, expected=202)
        data = {}

        if ok:
            job_id = self.job_id_from_header(response)
            if not do_async:
                data = self.fetch_job(job_id)
            else:
                data = {"job_id": job_id}

        return CommandResult(data, None, None)