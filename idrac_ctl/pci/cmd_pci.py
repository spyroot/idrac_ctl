"""iDRAC pci device query command

Command provides the option to retrieve firmware setting from iDRAC and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command caller can save
to a file and consume asynchronously or synchronously.

Author Mus spyroot@gmail.com
"""
import asyncio
from abc import abstractmethod
from typing import Optional

from tqdm import tqdm

from idrac_ctl import Singleton, ApiRequestType, IDracManager, save_if_needed, CommandResult


class PciDeviceQuery(IDracManager,
                     scm_type=ApiRequestType.PciDeviceQuery,
                     name='pci_device_query',
                     metaclass=Singleton):
    """
    Command implementation to get pci device and pci functions.
    """

    def __init__(self, *args, **kwargs):
        super(PciDeviceQuery, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument('pci_type', choices=['PCIeDevices', 'PCIeFunctions'],
                                default="PCIeDevices",
                                help="either pci device or pci function")

        help_text = "command fetch the pci device or function"
        return cmd_parser, "pci", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                pci_type: Optional[str] = "PCIeDevices",
                **kwargs) -> CommandResult:
        """Query pci device or function from idrac.
        :param verbose:
        :param do_async:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type: a data serialized back.
        :param pci_type: PCIeDevices or  PCIeFunctions
        :return: in data type json will return json
        """

        if verbose:
            print(f"cmd args data_type: {data_type} "
                  f"filename:{filename} do_async:{do_async} dev:{pci_type}")
            print(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"https://{self.idrac_ip}/redfish/v1/Systems/" \
            f"System.Embedded.1?$select={pci_type}"

        if not do_async:
            response = self.api_get_call(r, headers)
            self.default_error_handler(response)
        else:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self.api_async_get_until_complete
                (r, headers)
            )

        data = response.json()
        pci_data = []
        if pci_type in data:
            api_endpoints = data[pci_type]
            with tqdm(total=len(api_endpoints)) as pbar:
                for r in api_endpoints:
                    r = f"https://{self.idrac_ip}{r['@odata.id']}"
                    if not do_async:
                        response = self.api_get_call(r, headers)
                        self.default_error_handler(response)
                    else:
                        loop = asyncio.get_event_loop()
                        response = loop.run_until_complete(self.api_async_get_until_complete(r, headers))
                    pci_data.append(response.json())
                    pbar.update(1)

        save_if_needed(filename, pci_data)
        return CommandResult(pci_data, None, None)
