"""iDRAC query account services

Command query account services.

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional

from idrac_ctl.idrac_shared import IDRAC_API
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class QueryAccountService(IDracManager,
                          scm_type=ApiRequestType.QueryAccountService,
                          name='query_idrac',
                          metaclass=Singleton):
    """A command query iDRAC resource based on a resource path.
    """

    def __init__(self, *args, **kwargs):
        super(QueryAccountService, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command query account service."
        return cmd_parser, "account-svc", help_text

    def execute(self,
                resource: str,
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
        return self.base_query(IDRAC_API.AccountService,
                               filename=filename,
                               do_async=do_async,
                               do_expanded=do_expanded)
