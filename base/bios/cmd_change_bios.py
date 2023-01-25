"""iDRAC query bios registry

Command provides raw query bios registry.
python idrac_ctl.py bios-registry --attr_name SystemServiceTag,OldSetupPassword

Will return SystemServiceTag,OldSetupPassword and list of all attributes.

python idrac_ctl.py bios-registry --attr_list --attr_name SystemServiceTag,OldSetupPassword

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from base import Singleton, ApiRequestType, IDracManager, CommandResult, UnexpectedResponse, InvalidArgument
from base.shared import ScheduleJobType


class BiosChangeSettings(IDracManager, scm_type=ApiRequestType.BiosChangeSettings,
                         name='bios_change_settings',
                         metaclass=Singleton):
    """A command changes bios settings
    """
    def __init__(self, *args, **kwargs):
        super(BiosChangeSettings, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()

        cmd_parser.add_argument('--attr_name', type=str,
                                required=True, dest="attr_name", metavar="attribute name",
                                default=None,
                                help="attribute name or list. Example --attr_name MemTest,EmbSata")

        cmd_parser.add_argument('--attr_value', type=str,
                                required=True, dest="attr_value", metavar="attribute value",
                                default=None,
                                help="attribute name or list. Example --attr_values Disabled,RaidMode")

        help_text = "command change bios values"
        return cmd_parser, "bios-change", help_text

    @staticmethod
    def crete_bios_config(current_config, attr_name, attr_val) -> dict:
        """Create new config for a bios.
        :param current_config:
        :param attr_name:
        :param attr_val:
        :return:
        """

        bios_payload = {
            "Attributes": {
            }
        }

        attribute_names = []
        attribute_values = []

        if attr_name is not None and len(attr_name) > 0:
            if "," in attr_name:
                attribute_names = attr_name.split(",")
            else:
                attribute_names = [attr_name]

        if attr_val is not None and len(attr_val) > 0:
            if "," in attr_val:
                attribute_values = attr_val.split(",")
            else:
                attribute_values = [attr_val]

        if len(attribute_names) != len(attribute_values):
            raise InvalidArgument("Number of attribute and values mismatched.")

        for name, val in zip(attribute_names, attribute_values):
            bios_payload["Attributes"][name.strip()] = val.strip()

        for k, v in bios_payload["Attributes"].items():
            for current_data in current_config:
                if k in current_data.values() and current_data['Type'] == "Integer":
                    bios_payload['Attributes'][k] = int(v)

        return bios_payload

    def execute(self,
                attr_name: Optional[str] = None,
                attr_value: Optional[str] = None,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes command to change bios settings.

        :param attr_value:  attribute value or list of values
        :param attr_name: attribute name or list of values
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = "/redfish/v1/Systems/System.Embedded.1/Bios/BiosRegistry"
        cmd_result = self.base_query(target_api,
                                     filename=filename,
                                     do_async=do_async,
                                     do_expanded=do_expanded)

        registry = cmd_result.data['RegistryEntries']
        attribute_data = registry['Attributes']

        payload = self.crete_bios_config(attribute_data, attr_name, attr_value)
        base_payload = self.schedule_job(ScheduleJobType.OnReset, start_time=None, duration_time=None)
        base_payload.update(payload)

        target_api = "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"
        api_result = self.base_patch(target_api, payload=payload,
                                     do_async=do_async, expected_status=200)
        result = api_result.data
        if api_result is not None and api_result.extra is not None:
            resp = api_result.extra
            data = api_result.extra.json()
            self.default_json_printer(data)
            try:
                job_id = self.job_id_from_header(resp)
                if job_id is not None:
                    data = self.fetch_job(job_id)
                    result = data
            except UnexpectedResponse as ur:
                pass

        return CommandResult(result, None, None)