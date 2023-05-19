"""iDRAC clear pending values.

Command provides the option to clear all the pending attributes values.

Author Mus spyroot@gmail.com
"""
import argparse
from abc import abstractmethod
from typing import Optional


from ..cmd_exceptions import InvalidJsonSpec, FailedDiscoverAction
from ..cmd_utils import from_json_spec
from ..idrac_shared import IdracApiRespond
from ..redfish_shared import RedfishJson
from ..cmd_utils import str2bool
from ..idrac_shared import IdracApiRespond, ResetType
from ..cmd_utils import save_if_needed
from ..cmd_exceptions import InvalidArgument
from ..idrac_manager import IDracManager
from ..idrac_shared import IdracApiRespond, Singleton, ApiRequestType
from ..redfish_manager import CommandResult
from ..idrac_shared import IDRAC_API
from ..idrac_shared import IdracApiRespond


class AttributeClearPending(IDracManager,
                            scm_type=ApiRequestType.AttributeClearPending,
                            name='clear_pending',
                            metaclass=Singleton):
    """
    This cmd action is used to clear all the pending
    values currently in iDRAC.
    """

    def __init__(self, *args, **kwargs):
        super(AttributeClearPending, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command
        :param cls:
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)

        cmd_parser.add_argument(
            '--async', default=False, required=False,
            action='store_true', dest="do_async",
            help="Will use asyncio.")

        help_text = "command clear attribute pending values"
        return cmd_parser, "attr-clear-pending", help_text

    def execute(self,
                do_async: Optional[bool] = False,
                data_type: Optional[str] = "json",
                **kwargs
                ) -> CommandResult:
        """Execute clear pending command.
        :param do_async:
        :param data_type:
        :param kwargs:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        target = None
        attributes_cmd = self.sync_invoke(
            ApiRequestType.AttributesQuery,
            "attribute_inventory", do_deep=True
        )
        if attributes_cmd.error is not None:
            return attributes_cmd

        if isinstance(attributes_cmd.extra, list):
            for extra in attributes_cmd.extra:
                if RedfishJson.Actions in extra:
                    actions = extra[RedfishJson.Actions]
                    if '#DellManager.ClearPending' in actions:
                        target = actions['#DellManager.ClearPending']['target']

        if target is None:
            raise FailedDiscoverAction(
                "Failed discover clear pending attribute action."
            )

        cmd_result, api_resp = self.base_post(target, do_async=do_async)
        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = cmd_result.data['task_id']
            task_state = self.fetch_task(task_id)
            cmd_result.data['task_state'] = task_state
            cmd_result.data['task_id'] = task_id

        return cmd_result
