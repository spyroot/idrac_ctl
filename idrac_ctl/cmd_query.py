"""iDRAC query command

Command provides capability raw query based URI resource,
in case specific action might not implement yet; hence it
is easy to query.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from .cmd_utils import save_if_needed, find_ids
from .redfish_manager import CommandResult
from .cmd_exceptions import FailedDiscoverAction
from .cmd_exceptions import InvalidArgument
from .cmd_exceptions import UnsupportedAction
from .idrac_manager import IDracManager
from .idrac_shared import IdracApiRespond, Singleton, ApiRequestType
from .idrac_shared import IDRAC_JSON


from .redfish_shared import RedfishApi, RedfishJsonMessage
from .redfish_shared import RedfishApiRespond
from .redfish_shared import RedfishJsonSpec

from .cmd_exceptions import AuthenticationFailed
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import TaskIdUnavailable
from .cmd_utils import save_if_needed
from .redfish_respond import RedfishRespondMessage
from .redfish_respond_error import RedfishError

from .redfish_exceptions import RedfishForbidden
from .redfish_exceptions import RedfishMethodNotAllowed
from .redfish_exceptions import RedfishNotAcceptable
from .redfish_exceptions import RedfishUnauthorized
from .redfish_shared import RedfishJson

class QueryIDRAC(IDracManager,
                 scm_type=ApiRequestType.QueryIdrac,
                 name='query_idrac',
                 metaclass=Singleton):
    """A command query iDRAC resource based on a resource path.
    """

    def __init__(self, *args, **kwargs):
        super(QueryIDRAC, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        cmd_parser.add_argument(
            '-r', '--resource', required=True, dest="resource",
            type=str, default=None,
            help="Job id. Example /redfish/v1/Managers")
        help_text = "command query based on resource."
        return cmd_parser, "query", help_text

    def execute(self, resource: str,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes query command
        python idrac_ctl.py query

        :param resource: path to a resource
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        return self.base_query(resource,
                               filename=filename,
                               do_async=do_async,
                               do_expanded=do_expanded)
