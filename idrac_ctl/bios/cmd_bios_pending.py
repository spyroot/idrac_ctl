"""iDRAC query chassis services

Command provides raw query chassis and provide
list of supported actions.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from ..redfish_shared import RedfishJson

from ..redfish_manager import CommandResult
from ..cmd_exceptions import FailedDiscoverAction
from ..cmd_exceptions import InvalidArgument
from ..cmd_exceptions import UnsupportedAction
from ..idrac_manager import IDracManager
from ..idrac_shared import IdracApiRespond, Singleton, ApiRequestType
from ..idrac_shared import IDRAC_JSON


class BiosQueryPending(IDracManager,
                       scm_type=ApiRequestType.BiosQueryPending,
                       name='bios_query_pending',
                       metaclass=Singleton):
    """A command query job_service_query.
    """

    def __init__(self, *args, **kwargs):
        super(BiosQueryPending, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument(
            '-r', '--filter', required=False,
            dest="data_filter", type=str, default="",
            help="filter on pending value. (Example -r SriovGlobalEnable)"
        )

        help_text = "command query for bios pending values"
        return cmd_parser, "bios-pending", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                data_filter: Optional[str] = None,
                **kwargs) -> CommandResult:
        """Executes bios for pending changes.

        :param data_filter:
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded: will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        target_api = "/redfish/v1/Systems/System.Embedded.1/Bios/Settings"
        if data_filter:
            do_expanded = True

        cmd_result = self.base_query(
            target_api, filename=filename,
            do_async=do_async, do_expanded=do_expanded
        )
        if cmd_result.error is not None:
            return cmd_result

        if cmd_result.data is not None and RedfishJson.Attributes in cmd_result.data:
            attr_data = cmd_result.data[RedfishJson.Attributes]
            attr_cmd = CommandResult(attr_data, None, None, None)
            if data_filter is not None and len(data_filter) > 0:
                if data_filter in attr_data:
                    return CommandResult(
                        attr_data[data_filter], None, None, None
                    )
            else:
                cmd_result = attr_cmd

        return cmd_result
