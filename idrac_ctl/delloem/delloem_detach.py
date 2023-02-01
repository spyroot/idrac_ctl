"""iDRAC Redfish API with Dell OEM extension to detach network iso.

python idrac_ctl.py oem-detach

Author Mus spyroot@gmail.com
"""
from abc import abstractmethod
from typing import Optional
from idrac_ctl import Singleton, ApiRequestType, IDracManager, CommandResult


class DellOemDetach(IDracManager,
                    scm_type=ApiRequestType.DellOemDetach,
                    name='delloem_detach',
                    metaclass=Singleton):
    """A command uses dell oem to attach ISO
    """

    def __init__(self, *args, **kwargs):
        super(DellOemDetach, self).__init__(*args, **kwargs)

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser(is_remote_share=False)
        help_text = "command detach network iso"
        return cmd_parser, "oem-detach", help_text

    def execute(self,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes dell oem detach
        :param do_async: note async will subscribe to an event loop.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        cmd_result = self.sync_invoke(ApiRequestType.DellOemActions, "dell_oem_actions")
        redfish_action = cmd_result.discovered['DetachISOImage']
        target_api = redfish_action.target

        api_result = self.base_post(target_api,
                                    do_async=do_async, expected_status=200)
        return CommandResult(api_result.data, None, None)
