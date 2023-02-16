"""iDRAC query bios registry

Command provides capability to change bios settings
from JSON spec or via command line via --attr_name and comma separate list
of BIOS options and --attr_value.

Example:

idrac_ctl bios-change --from_spec ./test.spec.json --show on-reset

{
        "Attributes": {
                "MemFrequency": "MaxPerf",
                        "MemTest": "Disabled",
                        "OsWatchdogTimer": "Disabled",
                        "ProcCStates": "Disabled",
                        "SriovGlobalEnable": "Enabled"
        }
}

Author Mus spyroot@gmail.com
"""
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult
from idrac_ctl.cmd_exceptions import InvalidArgument
from idrac_ctl.cmd_exceptions import InvalidJsonSpec
from idrac_ctl.cmd_exceptions import UncommittedPendingChanges
from idrac_ctl.cmd_utils import from_json_spec
from idrac_ctl.idrac_shared import IDRAC_JSON
from idrac_ctl.idrac_shared import IdracApiRespond
from idrac_ctl.idrac_shared import IDRAC_API


class BiosChangeSettings(IDracManager,
                         scm_type=ApiRequestType.BiosChangeSettings,
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
        cmd_parser = cls.base_parser(is_reboot=True, is_expanded=False)

        bios_group = cmd_parser.add_argument_group('bios', '# BIOS attribute options')
        mt_group = cmd_parser.add_argument_group('maintenance', '# Maintenance related options')
        spec_from_group = cmd_parser.add_argument_group('json', '# JSON from a spec options')

        bios_group.add_argument(
            '--attr_name',
            help="attribute name or list. Example --attr_name MemTest,EmbSata",
            type=str, required=False, dest="attr_name", metavar="attribute name",
            default=None
        )

        bios_group.add_argument(
            '--attr_value',
            help="attribute name or list. Example --attr_values Disabled,RaidMode",
            type=str, required=False, dest="attr_value", metavar="attribute value",
            default=None
        )

        cmd_parser.add_argument(
            'apply',
            help='''choose when to apply a change.
            maintenance will create a future task,
            on-reset will apply on next rest.
            ''',
            choices=['on-reset', 'auto-boot', 'maintenance'],
            default="on-reset")

        mt_group.add_argument(
            "--start_date",
            help='''The start of maintenance window format YYYY-MM-DD
            This will create a future task.
            ''',
            required=False,
            dest="start_date", metavar="start date",
            type=str
        )

        mt_group.add_argument(
            "--start_time",
            help='''
            The start of maintenance window format HH:MM:SS \n
            This will create a future task.
            ''',
            required=False, default="00:00:00",
            dest="start_time", metavar="start time",
            type=str
        )

        mt_group.add_argument(
            '--duration',
            help="maximum duration for a maintenance window from a start time",
            type=int, required=False,
            dest="default_duration",
            metavar="duration",
            default=600
        )

        cmd_parser.add_argument(
            '--show', action='store_true',
            required=False, dest="do_show", default=False,
            help="will only show and will not apply any changes.."
        )

        cmd_parser.add_argument(
            '-c', '--commit', action='store_true',
            required=False, dest="do_commit", default=False,
            help="by default bios change created in pending state, "
                 "hence we can cancel, otherwise pass --commit or -c"
        )

        cmd_parser.add_argument(
            '--commit_pending', action='store_true',
            required=False, default=False,
            help="if idrac already container pending value, this option "
                 "will commit change and reboot host")

        spec_from_group.add_argument(
            '-s', '--from_spec',
            help="Read json spec for new bios attributes,  "
                 "(Example --from_spec new_bios.json)",
            type=str, required=True, dest="from_spec", metavar="file name",
            default=None
        )

        help_text = "command change bios configuration attributes"
        return cmd_parser, "bios-change", help_text

    @property
    def ok(self):
        """Accepted; a Task has been generated"""
        return 202

    @property
    def accepted(self):
        """Accepted; a Task has been generated"""
        return 202

    @property
    def success(self):
        """Success, but no response data
        :return:
        """
        return 204

    @staticmethod
    def crete_bios_config(current_config, attr_name, attr_val) -> dict:
        """Create new config for a bios.
        :param current_config:
        :param attr_name: bios attribute name
        :param attr_val: bios attribute value
        :return: a dict
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
            raise InvalidArgument("Number of attribute "
                                  "and values mismatched.")

        for name, val in zip(attribute_names, attribute_values):
            bios_payload["Attributes"][name.strip()] = val.strip()

        for k, v in bios_payload[IDRAC_JSON.Attributes].items():
            for current_data in current_config:
                if k in current_data.values() and current_data['Type'] == "Integer":
                    bios_payload[IDRAC_JSON.Attributes][k] = int(v)

        return bios_payload

    def execute(self,
                attr_name: Optional[str] = None,
                attr_value: Optional[str] = None,
                apply: Optional[str] = "on-reset",
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_reboot: Optional[bool] = False,
                do_show: Optional[bool] = False,
                do_commit: Optional[bool] = False,
                commit_pending: Optional[bool] = False,
                start_date: Optional[str] = "",
                start_time: Optional[str] = "",
                from_spec: Optional[str] = "",
                default_duration: Optional[int] = 600,
                **kwargs) -> CommandResult:
        """Executes command to change bios settings.

        :param do_reboot:
        :param default_duration:
        :param apply:
        :param do_show: will only show final spec but will not apply any changes.
        :param do_commit: by default value are in pending state.
        :param attr_value:  attribute value or list of values
        :param attr_name: attribute name or list of values
        :param do_async: note async will subscribe to an event loop.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param from_spec: read bios changes from a spec file
        :param commit_pending:  this command will first commit all pending changes before do new change.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :param start_time:
        :param start_date:
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = f"{self.idrac_manage_servers}{IDRAC_API.BIOS_REGISTRY}"
        cmd_result = self.base_query(
            target_api, filename=filename,
            do_async=do_async, do_expanded=False
        )
        if verbose:
            self.default_json_printer(cmd_result.data)

        if IDRAC_JSON.RegistryEntries not in cmd_result.data:
            return CommandResult(
                {"Status": "Failed fetch bios registry"}, None, None, None)
        registry = cmd_result.data[IDRAC_JSON.RegistryEntries]

        if IDRAC_JSON.Attributes not in cmd_result.data:
            return CommandResult(
                {"Status": "Failed fetch attributes from bios registry"}, None, None, None)
        attribute_data = registry[IDRAC_JSON.Attributes]

        # we read either from a file or form args
        # comma seperated.
        try:
            if from_spec is not None and len(from_spec) > 0:
                payload = from_json_spec(from_spec)
            else:
                payload = self.crete_bios_config(
                    attribute_data, attr_name, attr_value
                )
            if len(payload) == 0:
                return CommandResult(self.api_is_change_msg(False), None, None, None)
        except json.decoder.JSONDecodeError as jde:
            raise InvalidJsonSpec(
                "It looks like your JSON spec is invalid. "
                "JSONlint the file and check..".format(str(jde)))

        job_req_payload = self.create_apply_time_req(
            apply, start_time, start_date, default_duration)
        payload.update(job_req_payload)
        if verbose:
            self.logger.info(f"payload: {payload}")

        if do_show:
            return CommandResult(payload, None, None, None)

        cmd_pending = self.sync_invoke(
            ApiRequestType.BiosQueryPending, "bios_query_pending",
        )

        # commit or not pending
        if len(cmd_pending.data) > 0:
            if commit_pending:
                cmd_apply = self.sync_invoke(
                    ApiRequestType.JobApply,
                    "job_apply", do_reboot=True, setting="bios",
                )
                print("Applied change", cmd_apply.data)
            else:
                raise UncommittedPendingChanges(
                    "BIOS contains pending changes in the queue. "
                    "Please apply changes first."
                )

        # update bios.
        target_api = f"{self.idrac_manage_servers}{IDRAC_API.BiosSettings}"
        cmd_result, api_resp = self.base_patch(
            target_api, payload=payload,
            do_async=do_async
        )

        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            task_state = self.fetch_task(task_id)
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = task_id
        else:
            # here we have 4 mutually exclusive option
            # either we commit all pending, reset jobs, or cancel or just submit.
            if api_resp.Success or api_resp.Ok:
                if do_commit:
                    # we commit with a reboot
                    cmd_apply = self.sync_invoke(
                        ApiRequestType.JobApply,
                        "job_apply", do_reboot=do_reboot, do_watch=True,
                    )
                    if cmd_apply.error is not None:
                        return cmd_apply
            # if do_reset:
            #     cmd_apply = self.sync_invoke(
            #         ApiRequestType.JobApply,
            #         "job_apply", do_reboot=do_reboot, do_watch=True,
            #     )
            # if do_cancel:
            #     cmd_apply = self.sync_invoke(
            #         ApiRequestType.JobApply,
            #         "job_apply", do_reboot=do_reboot, do_watch=True,
            #     )
            # if just_do:

        if do_reboot:
            self.reboot()

        return cmd_result
