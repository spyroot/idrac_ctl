"""iDRAC command clear boot source pending values.

Command provides the option to clear boot source pending values.
if values un committed.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import json
from abc import abstractmethod
from typing import Optional

from idrac_ctl import IDracManager, ApiRequestType, Singleton, CommandResult
from idrac_ctl.idrac_manager import PostRequestFailed


class BootSourceClearPending(IDracManager, scm_type=ApiRequestType.BootSourceClear,
                             name='clear_pending',
                             metaclass=Singleton):
    """
    This cmd action is used to clear all BIOS pending
    values currently in iDRAC.
    """

    def __init__(self, *args, **kwargs):
        super(BootSourceClearPending, self).__init__(*args, **kwargs)

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
                                help="will use asyncio.")

        help_text = "command clear boot source pending values"
        return cmd_parser, "boot-clear-pending", help_text

    def execute(self,
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """Execute clear boot source pending values.

        :param do_async:
        :param data_type:
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        api_target = "/redfish/v1/Systems/System.Embedded.1/Oem/Dell/DellBootSources" \
                     "/Settings/Actions/DellManager.ClearPending"

        ok = False
        api_req_result = {}
        try:
            pd = {}
            r = f"https://{self.idrac_ip}{api_target}"
            if not do_async:
                response = self.api_post_call(r, json.dumps(pd), headers)
                ok = self.default_post_success(self, response, expected=200)
                api_req_result["Response"] = response.status_code
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(self.async_post_until_complete(r, json.dumps(pd), headers))
        except PostRequestFailed as pf:
            print("Error:", pf)
            pass

        api_result = {"Status": ok}
        return CommandResult(api_result, None, None)
