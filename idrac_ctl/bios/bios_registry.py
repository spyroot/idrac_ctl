"""iDRAC query bios registry

Command provides raw query bios registry.
python idrac_ctl.py bios-registry --attr_name SystemServiceTag,OldSetupPassword

Will return SystemServiceTag,OldSetupPassword and list of all attributes.

python idrac_ctl.py bios-registry --attr_list --attr_name SystemServiceTag,OldSetupPassword

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult, save_if_needed


class BiosRegistry(IDracManager,
                   scm_type=ApiRequestType.BiosRegistry,
                   name='bios_registry',
                   metaclass=Singleton):
    """A command query job_service_query.
    """

    def __init__(self, *args, **kwargs):
        super(BiosRegistry, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument(
            '--registry_only',
            action='store_true',
            required=False, dest="is_registry_only",
            default=True,
            help="return only registry")

        cmd_parser.add_argument(
            '--attr_only',
            action='store_true',
            required=False, dest="is_attr_only",
            default=False,
            help="return only attribute")

        cmd_parser.add_argument(
            '--attr_name', type=str,
            required=False, dest="attr_name",
            default=None,
            help="attribute name or list. Example --attr_name SystemServiceTag,OldSetupPassword")

        cmd_parser.add_argument(
            '--attr_list', action='store_true',
            required=False, dest="attr_list",
            default=False,
            help="return list of all attribute names.")

        cmd_parser.add_argument(
            '--filter-read_only', action='store_true',
            required=False, dest="no_read_only",
            default=False,
            help="will filter out all read-only.")

        help_text = "command query bios registry"
        return cmd_parser, "bios-registry", help_text

    def execute(self,
                is_registry_only: Optional[bool] = False,
                is_attr_only: Optional[bool] = False,
                attr_name: Optional[str] = None,
                attr_list: Optional[bool] = False,
                no_read_only: Optional[bool] = False,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes query bios registry.

        :param no_read_only:  filters, remove all read only.
        :param attr_list: will also return list of all attributes
        :param attr_name: will filler based on attribute names.
        :param is_registry_only: will return complete registry. (Default)
        :param is_attr_only: will return all attributes
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = "/redfish/v1/Systems/System.Embedded.1/Bios/BiosRegistry"
        cmd_result = self.base_query(target_api,
                                     filename=None,
                                     do_async=do_async,
                                     do_expanded=do_expanded)

        filtered_result = []
        attribute_names = None

        registry = cmd_result.data['RegistryEntries']
        data = registry['Attributes']

        if attr_list:
            if isinstance(data, list):
                attribute_names = [d['AttributeName'] for d in data]

        if attr_name is not None and len(attr_name) > 0:
            if "," in attr_name:
                attr_names = attr_name.split(",")
            else:
                attr_names = [attr_name]

            # filter by attribute name
            if isinstance(data, list):
                for n in attr_names:
                    for entry in data:
                        if entry['AttributeName'] == n:
                            # entry_dict.update(entry)
                            filtered_result.append(entry)
                            break
                data = filtered_result
            elif isinstance(data, dict):
                data = data[attr_name]
        else:
            if is_registry_only:
                data = cmd_result.data['RegistryEntries']
            if is_registry_only:
                registry = cmd_result.data['RegistryEntries']
                data = registry['Attributes']

        filtered_read_only = []
        if no_read_only:
            if 'RegistryEntries' in data:
                source_data = registry['RegistryEntries']['Attributes']
            elif 'Attributes' in data:
                source_data = registry['Attributes']
            elif isinstance(data, list):
                source_data = data
            else:
                raise ValueError("unknown value.")

            for entry in source_data:
                if entry['ReadOnly']:
                    continue
                else:
                    filtered_read_only.append(entry)
            data = filtered_read_only

        save_if_needed(filename, data)

        return CommandResult(data, None, attribute_names)
