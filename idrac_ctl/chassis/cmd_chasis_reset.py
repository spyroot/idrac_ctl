"""iDRAC reset a chassis power state.

 idrac_ctl chassis-reset --reset_type ForceOff

Author Mus spyroot@gmail.com
"""
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl import CommandResult
from idrac_ctl.cmd_exceptions import FailedDiscoverAction, PostRequestFailed, UnsupportedAction
from idrac_ctl.cmd_exceptions import InvalidArgument


class ChassisReset(IDracManager,
                   scm_type=ApiRequestType.ChassisReset,
                   name='reboot',
                   metaclass=Singleton):
    """
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
                                help="On, ForceOff. On will change power state on.")

        help_text = "command change power state of a chassis"
        return cmd_parser, "chassis-reset", help_text

    def execute(self,
                reset_type: Optional[str] = "On",
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """
        :param do_async:
        :param data_type:
        :param reset_type: "On, ForceOff"
        :param kwargs:
        :return: return cmd result
        :raise FailedDiscoverAction
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        chassis_data = self.sync_invoke(
            ApiRequestType.ChassisQuery, "chassis_service_query", do_expanded=True
        )

        if 'Reset' not in chassis_data.discovered:
            raise UnsupportedAction("Failed to discover the reset chassis action")

        redfish_action = chassis_data.discovered['Reset']
        target_api = redfish_action.target
        args = redfish_action.args
        args_options = args['ResetType']
        if reset_type not in args_options:
            raise InvalidArgument(f"Unsupported reset type {reset_type} "
                                  f"supported reset options {args_options}.")

        if target_api is None:
            FailedDiscoverAction("Failed discover reset chassis actions.")

        payload = {'ResetType': reset_type}
        r = f"https://{self.idrac_ip}{target_api}"

        ok = False
        try:
            if not do_async:
                response = self.api_post_call(r, json.dumps(payload), headers)
                ok = self.default_post_success(self, response)
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(
                    self.async_post_until_complete(r, json.dumps(payload), headers)
                )
        except PostRequestFailed as prf:
            print(prf)
            pass

        return CommandResult(self.api_success_msg(ok), None, None)
