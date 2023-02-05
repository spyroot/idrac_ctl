"""iDRAC command clear bios pending values.

Command provides the option to clear all the BIOS
pending values.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton, CommandResult
from idrac_ctl.cmd_exceptions import FailedDiscoverAction
from idrac_ctl.idrac_manager import PostRequestFailed


class BiosClearPending(IDracManager,
                       scm_type=ApiRequestType.BiosClearPending,
                       name='clear_pending',
                       metaclass=Singleton):
    """
    This cmd action is used to clear all BIOS pending
    values currently in iDRAC.
    """

    def __init__(self, *args, **kwargs):
        super(BiosClearPending, self).__init__(*args, **kwargs)

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

        help_text = "command clear bios pending values"
        return cmd_parser, "bios-clear-pending", help_text

    def execute(self,
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """Execute clear BIOS pending values

        :param do_async:
        :param data_type:
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        cmd_result = self.sync_invoke(ApiRequestType.BiosQuery,
                                      "bios_inventory", do_deep=True)
        api_target = None
        if cmd_result.discovered is not None and \
                'ClearPending' in cmd_result.discovered:
            api_target = cmd_result.discovered['ClearPending'].target

        if api_target is None:
            raise FailedDiscoverAction("Failed discover clear pending bios action.")

        api_req_result = {}
        try:
            pd = {}
            r = f"https://{self.idrac_ip}{api_target}"
            if not do_async:
                response = self.api_post_call(r, json.dumps(pd), headers)
                ok = self.default_post_success(self, response, expected=200)
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(self.async_post_until_complete(r, json.dumps(pd), headers))
            api_req_result = {"Status": ok}

        except PostRequestFailed as pf:
            self.logger.error(pf)

        return CommandResult(api_req_result, None, None)
