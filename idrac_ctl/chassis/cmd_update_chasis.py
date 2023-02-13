"""iDRAC reset a chassis power state.

The Chassis schema represents the physical components of a system.
This resource represents the sheet-metal confined spaces
and logical zones such as racks, enclosures, chassis and all other
containers. Subsystems, such as sensors, that operate outside a system's
data plane are linked either directly or indirectly through this resource.
A subsystem that operates outside a system's data plane are not
accessible to software that runs on the system.

 idrac_ctl chassis-update

Author Mus spyroot@gmail.com
"""
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl.cmd_exceptions import FailedDiscoverAction, InvalidJsonSpec
from idrac_ctl.cmd_exceptions import PostRequestFailed
from idrac_ctl.cmd_exceptions import UnsupportedAction
from idrac_ctl.cmd_exceptions import InvalidArgument
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.shared import IDRAC_API
from idrac_ctl.cmd_utils import from_json_spec


class ChassisReset(IDracManager,
                   scm_type=ApiRequestType.ChassisReset,
                   name='update_chassis',
                   metaclass=Singleton):
    """
    This  action update chassis .
    """

    def __init__(self, *args, **kwargs):
        super(ChassisReset, self).__init__(*args, **kwargs)

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
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_file_save=False, is_expanded=False)
        chassis_group = cmd_parser.add_argument_group('chassis', '# chassis related options')

        chassis_group.add_argument(
            '--chassis_id', required=True, dest='reset_type',
            default=None, type=str, help="chassis id.")

        chassis_group.add_argument(
            '-s', '--from_spec',
            help="Read json spec for new bios attributes,  "
                 "(Example --from_spec new_bios.json)",
            type=str, required=True, dest="from_spec", metavar="file name",
            default=None
        )

        help_text = "command update chassis"
        return cmd_parser, "chassis-reset", help_text

    def execute(self,
                chassis_id,
                from_spec: Optional[str] = "",
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """
        :param chassis_id of the property of the Chassis resource
        :param from_spec:  a path to json spec file
        :param do_async: optional for asyncio
        :param data_type: a data type
        :param kwargs: the rest args
        :return: return cmd result
        :raise FailedDiscoverAction
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)


        try:
            if from_spec is not None and len(from_spec) > 0:
                payload = from_json_spec(from_spec)
                if len(payload) == 0:
                    return CommandResult(
                        self.api_is_change_msg(False), None, None, None)

                r = f"{IDRAC_API.Chassis}{chassis_id}"
                self.base_patch(r, payload=payload, do_async=do_async, data_type=data_type)
        except json.decoder.JSONDecodeError as jde:
            raise InvalidJsonSpec(
                "It looks like your JSON spec is invalid. "
                "JSONlint the file and check..".format(str(jde)))


        self.ba
        payload = {'ResetType': reset_type}
        ok = False
        try:
            if not do_async:
                response = self.api_patch_call(
                    r, json.dumps(payload), headers
                )
                ok = self.api_patch_call(
                    self, response, ignore_error_code=409
                )
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(
                    self.async_post_until_complete(
                        r, json.dumps(payload), headers,
                        ignore_error_code=409
                    )
                )

            if ok:
                job_id = self.parse_task_id(response)
                self.logger.info(f"job id: {job_id}")
                if len(job_id) > 0:
                    self.fetch_task(job_id)

        except PostRequestFailed as prf:
            self.logger.error(prf)

        return CommandResult(self.api_success_msg(ok), None, None, None)
