"""iDRAC clear pending values.

Command provides the option to clear all the pending values.
Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from base import IDracManager, ApiRequestType, Singleton, CommandResult
from base.idrac_manager import UnsupportedAction, PostRequestFailed


class ClearPending(IDracManager, scm_type=ApiRequestType.ClearPending,
                   name='clear_pending',
                   metaclass=Singleton):
    """
    This cmd action is used to clear all the pending
    values currently in iDRAC.
    """

    def __init__(self, *args, **kwargs):
        super(ClearPending, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)

        cmd_parser.add_argument('--async', default=False, required=False,
                                action='store_true', dest="do_async",
                                help="Will use asyncio.")

        help_text = "clear pending values."
        return cmd_parser, "clear_pending", help_text

    def execute(self,
                filename: Optional[str] = None,
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """Execute clear pending command.
        :param do_async:
        :param filename:
        :param data_type:
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target = None
        attributes_cmd = self.sync_invoke(ApiRequestType.AttributesQuery,
                                          "attribute_inventory", do_deep=True)
        if isinstance(attributes_cmd.extra, list):
            for extra in attributes_cmd.extra:
                if 'Actions' in extra:
                    actions = extra['Actions']
                    if '#DellManager.ClearPending' in actions:
                        target = actions['#DellManager.ClearPending']['target']

        api_req_result = {}
        if target is not None:
            try:
                pd = {}
                r = f"https://{self.idrac_ip}{target}"
                if not do_async:
                    response = self.api_post_call(r, json.dumps(pd), headers)
                    ok = self.default_post_success(self, response, expected=200)
                    api_req_result = {"Status": ok}
                else:
                    loop = asyncio.get_event_loop()
                    ok = loop.run_until_complete(self.api_async_post_until_complete(r, json.dumps(pd), headers))
                    api_req_result = {"Status": ok}

            except PostRequestFailed as pf:
                print("Error:", pf)
                pass
        else:
            raise UnsupportedAction("Clear pending unsupported.")

        return CommandResult(api_req_result, None, None)
