"""iDRAC reset a chassis power state.

 idrac_ctl chassis-reset --reset_type ForceOff

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.cmd_exceptions import FailedDiscoverAction
from idrac_ctl.cmd_exceptions import InvalidArgument
from idrac_ctl.cmd_exceptions import UnsupportedAction
from idrac_ctl.idrac_shared import IdracApiRespond
from idrac_ctl.idrac_shared import IDRAC_JSON


class ChassisReset(IDracManager,
                   scm_type=ApiRequestType.ChassisReset,
                   name='reboot',
                   metaclass=Singleton):
    """
    This  action resets the chassis but does not reset systems
    or other contained resources, although side effects can occur
    that affect those resources.
    """

    def __init__(self, *args, **kwargs):
        super(ChassisReset, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_file_save=False, is_expanded=False)
        cmd_parser.add_argument('--reset_type',
                                required=False, dest='reset_type',
                                default="On", type=str,
                                help="On, ForceOff. On will change power state..")

        help_text = "command change power state of a chassis"
        return cmd_parser, "chassis-reset", help_text

    def discover_reset(self, reset_type) -> str:
        """Method discover reset action, and return target api
        in order invoke reset.
        :param reset_type:
        :return: discovered action
        :raise InvalidArgument if reset type unknown
        """
        chassis_data = self.sync_invoke(
            ApiRequestType.ChassisQuery, "chassis_service_query",
            do_expanded=True
        )

        if 'Reset' not in chassis_data.discovered:
            raise UnsupportedAction(
                "Failed to discover the reset chassis action"
            )

        redfish_action = chassis_data.discovered[IDRAC_JSON.Reset]
        target_api = redfish_action.target
        args = redfish_action.args
        args_options = args[IDRAC_JSON.ResetType]

        if reset_type not in args_options:
            raise InvalidArgument(
                f"Unsupported reset type {reset_type} "
                f"supported reset options {args_options}."
            )

        return target_api

    def execute(self,
                reset_type: Optional[str] = "On",
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                do_watch: Optional[str] = True,
                **kwargs
                ) -> CommandResult:
        """
        Execute command and change chassis power state.
        :param do_async: async or not
        :param data_type:
        :param reset_type: "On, ForceOff"
        :param do_watch: wait and watch progress.
        :param kwargs: args passwd downstream
        :return: return cmd result
        :raise FailedDiscoverAction
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target_api = self.discover_reset(reset_type)

        if target_api is None:
            FailedDiscoverAction(
                "Failed discover reset chassis actions."
            )

        payload = {IDRAC_JSON.ResetType: reset_type}
        cmd_result, api_resp = self.base_post(
            target_api, payload=payload, do_async=do_async
        )

        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            cmd_result.data['task_id'] = task_id

            if do_watch:
                task_state = self.fetch_task(task_id)
                cmd_result.data['task_state'] = task_state

        return CommandResult(self.api_success_msg(api_resp), None, None, None)
