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
                          name='query_account_svc',
                          metaclass=Singleton):
    """A command query iDRAC resource based on a resource path.
    """

    def __init__(self, *args, **kwargs):
        super(QueryAccountService, self).__init__(*args, **kwargs)
        # maps from cli choice to a key in respond
        self._json_filter_dict = {
            'account-type': 'SupportedAccountTypes',
            'oem_account-type': 'SupportedOEMAccountTypes',
            'accounts': 'Accounts',
            'ldap': 'LDAP',
            'ad': 'ActiveDirectory',
            'local': 'LocalAccountAuth',
            'lockout-reset-after': 'AccountLockoutCounterResetAfter',
            'lockout-duration': 'AccountLockoutDuration',
            'lockout-threshold': 'AccountLockoutThreshold',
            'status': 'Status',
            'roles': 'Roles'
        }

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command query account service."
        cmd_parser.add_argument('--filter', choices=['account-type',
                                                     'oem_account-type',
                                                     'accounts',
                                                     'ldap',
                                                     'ad',
                                                     'local',
                                                     'lockout-reset-after',
                                                     'lockout-duration',
                                                     'lockout-threshold',
                                                     'status',
                                                     'roles'],

                                default=None, required=False, dest="schema_filter",
                                help="filter show account types, ldap, roles etc")

        return cmd_parser, "account-svc", help_text

    def execute(self,
                schema_filter: Optional[str] = None,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes query command
        python idrac_ctl.py query

        :param schema_filter: filter account services based on schema filter key.
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        json_filter = ""
        is_expanded = False

        if schema_filter is not None and len(schema_filter) > 0 or do_expanded:
            is_expanded = True
            if schema_filter in self._json_filter_dict:
                json_filter = self._json_filter_dict[schema_filter]

        cmd_result = self.base_query(IDRAC_API.AccountService,
                                     filename=filename,
                                     do_async=do_async,
                                     do_expanded=is_expanded)
        print(cmd_result.data.keys())

        if cmd_result.error is None:
            if len(json_filter) > 0 and json_filter in cmd_result.data:
                cmd_result = CommandResult(cmd_result.data[json_filter], None, None, None)

        return cmd_result
