"""iDRAC clear pending values.

Command provides the option to clear all the pending values.
Author Mus spyroot@gmail.com
"""
import argparse
import json
from abc import abstractmethod
from typing import Optional

from base import IDracManager, ApiRequestType, Singleton, CommandResult
from base.idrac_manager import UnsupportedAction, PostFailed


class ClearPending(IDracManager, scm_type=ApiRequestType.ClearPending,
                   name='clear_pending',
                   metaclass=Singleton):
    """
    This cmd action is used to clear all the pending values.
    """

    def __init__(self, *args, **kwargs):
        super(ClearPending, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser.add_argument('--async', action='store_true', required=False,
                                default="", help="Will reset and will not block. "
                                                 "By default wait task to complete")
        help_text = "reboots the system"
        return cmd_parser, "clear_pending", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """Execute attribute clear pending.

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

        if target is not None:
            try:
                r = f"https://{self.idrac_ip}{target}"
                response = self.api_post_call(r, json.dumps({}), headers)
                self.default_post_success(self, response, expected=200)
            except PostFailed as pf:
                print("Error:", pf)
                pass
        else:
            raise UnsupportedAction("Clear pending unsupported.")

        return CommandResult({}, None, None)
