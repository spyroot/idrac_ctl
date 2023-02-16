"""iDRAC attribute command

Command provides the option to retrieve the iDRAC attribute and serialize
back as caller as JSON, YAML, and XML. In addition, it automatically
registers to the command line ctl tool. Similarly to the rest command caller can save
to a file and consume asynchronously or synchronously.

python idrac_ctl.py --json attribute --filter ServerPwrMon.1.PeakCurrentTime

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional

from idrac_ctl import CommandResult
from idrac_ctl import IDracManager, ApiRequestType, Singleton
from idrac_ctl.cmd_exceptions import InvalidArgumentFormat
from idrac_ctl.cmd_utils import from_json_spec
from idrac_ctl.idrac_shared import IdracApiRespond


class AttributesUpdate(IDracManager,
                       scm_type=ApiRequestType.AttributesUpdate,
                       name='attribute_update',
                       metaclass=Singleton):
    """iDRAC Attribute Query Command, fetch attribute data, caller can save to a file
    or output to a file or pass downstream.
    """

    def __init__(self, *args, **kwargs):
        super(AttributesUpdate, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Registers command args
        :param cls:
        :return:
        """
        cmd_arg = argparse.ArgumentParser(add_help=False)

        cmd_arg.add_argument(
            '--async', action='store_true', required=False, dest="do_async",
            default=False, help="Will create a task and will not wait.")

        cmd_arg.add_argument(
            '-s', '--from_spec',
            help="Read json spec for new bios attributes,  "
                 "(Example --from_spec attribute.json)",
            type=str, required=True, dest="from_spec", metavar="file name",
            default=None
        )

        help_text = "command fetch the attribute view"
        return cmd_arg, "attr-update", help_text

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                from_spec: Optional[str] = "",
                **kwargs) -> CommandResult:
        """Queries attributes from iDRAC.
        :param from_spec:
        :param do_async:
        :param verbose:
        :param filename: if filename indicate call will save a bios setting to a file.
        :param data_type:
        :return:
        :raise: AuthenticationFailed, UnexpectedResponse
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        if from_spec is None or len(from_spec) == 0:
            raise InvalidArgumentFormat("from_spec is empty string")

        api_target = "/redfish/v1/Managers/System.Embedded.1/Attributes"

        payload = from_json_spec(from_spec)
        cmd_result, api_resp = self.base_patch(
            api_target, payload=payload,
            do_async=do_async
        )

        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            task_state = self.fetch_task(task_id)
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = task_id

        return cmd_result
