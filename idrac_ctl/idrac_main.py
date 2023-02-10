"""Main entry for idrac_ctl

The main routine for idrac_ctl , ctl tool leverages iDRAC Manager class.
to interact with Dell IDRAC.

Each command registered dynamically and dispatch to respected execute method
by invoking request from IDRAC Manager.

Author Mus spyroot@gmail.com
"""

import argparse
import collections
import json
import os
import ssl
import sys
import warnings
from typing import Optional, Dict

import requests
import urllib3
from pygments import highlight
import logging

try:
    from pygments.lexers.data import JsonLexer
except ImportError as ie:
    warnings.warn("Failed import json lexer from pygments.")

from pygments.formatters.terminal256 import Terminal256Formatter

from idrac_ctl.cmd_utils import save_if_needed
from idrac_ctl.shared import RedfishAction, RedfishActionEncoder
from idrac_ctl.cmd_exceptions import UnsupportedAction
from idrac_ctl.cmd_exceptions import InvalidArgument, FailedDiscoverAction
from idrac_ctl.cmd_exceptions import AuthenticationFailed, ResourceNotFound
from idrac_ctl.cmd_exceptions import InvalidJsonSpec, MissingMandatoryArguments
from idrac_ctl.cmd_exceptions import UncommittedPendingChanges
from idrac_ctl.cmd_exceptions import JsonHttpError
from idrac_ctl.idrac_manager import IDracManager
from idrac_ctl.idrac_manager import MissingResource
from idrac_ctl.idrac_manager import TaskIdUnavailable
from idrac_ctl.custom_argparser.customer_argdefault import CustomArgumentDefaultsHelpFormatter
from idrac_ctl import version

try:
    from urllib3.exceptions import InsecureRequestWarning

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError as ir:
    warnings.warn("Failed import urllib3")

logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s '
                           '[%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
logger.addHandler(console_handler)


class TermColors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


"note we do sub-string match"
TermList = ["xterm", "linux", "ansi", "xterm-256color"]


def color_printer(msg: str, tcolor: Optional[str] = TermColors.WARNING):
    """Printer error and if terminal support color print red or green etc.
    """
    current_term = os.getenv("TERM")
    if current_term is not None and current_term in TermList:
        err_msg = '{:<30}'.format(f"{tcolor}{msg}{TermColors.ENDC}")
        print(err_msg)
    else:
        print(msg)


def console_error_printer(msg):
    """Printer error and if terminal support color print red or green etc.
    """
    color_printer(msg, tcolor=TermColors.WARNING)


def formatter(prog):
    argparse.HelpFormatter(prog, max_help_position=100, width=200)


class IdracDetails:
    version = version.__version__
    description = 'iDRAC command line tools.'
    author = 'Mus'
    author_email = 'spyroot@gmail.com'


__version__ = IdracDetails.version


def log_verbose(cmd_args, err):
    if cmd_args.verbose:
        err_msg = str(err)
        warnings.warn(f"Failed parse server respond. {err_msg}")
    return


def json_printer(json_data,
                 cmd_args: argparse.Namespace,
                 sort: Optional[bool] = True,
                 indents: Optional[int] = 4,
                 colorized: Optional[bool] = True,
                 header: Optional[str] = None,
                 footer: Optional[str] = None) -> None:
    """Json stdout printer.
    :param cmd_args:
    :param header:
    :param footer:
    :param colorized:
    :param json_data:
    :param indents:
    :param sort:
    :return:
    """
    if cmd_args.no_stdout:
        return

    json_raw = {}
    try:
        if isinstance(json_data, RedfishAction):
            json_raw = json_data.toJSON()
        elif isinstance(json_data, requests.models.Response):
            header = json_data.headers
            content_type = header.get('content-type')
            if content_type is not None:
                json_raw = json_data.json()
        elif isinstance(json_data, str):
            json_raw = json.dumps(
                json.loads(json_data), sort_keys=sort, indent=indents
            )
        else:
            json_raw = json.dumps(
                json_data, sort_keys=sort, indent=indents,
                cls=RedfishActionEncoder
            )

        if len(json_raw) > 0:
            if header is not None and cmd_args.json_only is False:
                print(header)

            if colorized:
                colorful = highlight(
                    json_raw,
                    lexer=JsonLexer(),
                    formatter=Terminal256Formatter())
                print(colorful)
            else:
                print(json_raw)

            if footer is not None:
                print(footer)
    except AttributeError as attr_err:
        log_verbose(cmd_args, attr_err)
        return
    except requests.exceptions.JSONDecodeError as rjde:
        log_verbose(cmd_args, rjde)
        return
    except json.decoder.JSONDecodeError as jde:
        log_verbose(cmd_args, jde)
        return


def process_respond(cmd_args, command_result):
    """
    """
    query_request = {}
    if cmd_args.data_only:
        return command_result.data

    if command_result.data is not None:
        query_request["data"] = command_result.data
        query_request["idrac-data-description"] = "# idrac data for the command:"

    # extra data for deep walks
    if command_result.extra is not \
            None and cmd_args.no_extra is False:
        query_request["extra"] = command_result.extra
        query_request["idrac-extra-description"] = "# idrac extra data for the command:"
        # save extra as separate files.
        if hasattr(cmd_args, 'do_save') and cmd_args.do_save:
            for extra_k in command_result.extra.keys():
                if cmd_args.verbose:
                    logger.info(f"Saving {extra_k}.json")
                save_if_needed(f"{extra_k}.json", command_result.extra[extra_k])

    # discovered rest action.
    if command_result.discovered is not None and cmd_args.no_action is False:
        if cmd_args.json:
            if isinstance(command_result.discovered, dict):
                for ak in command_result.discovered.keys():
                    query_request["actions-description"] = "# Redfish actions:"
                    if isinstance(command_result.discovered[ak], RedfishAction):
                        query_request["actions"] = json.dumps(command_result.discovered[ak].__dict__)
                    else:
                        query_request["actions"] = command_result.discovered[ak]
            else:
                query_request["actions"] = command_result.discovered

    return query_request


def main(cmd_args: argparse.Namespace, command_name_to_cmd: Dict) -> None:
    """Main entry point
    """
    if cmd_args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # idrac manager main interface main uses to interact with IDRAC.
    redfish_api = IDracManager(idrac_ip=cmd_args.idrac_ip,
                               idrac_username=cmd_args.idrac_username,
                               idrac_password=cmd_args.idrac_password,
                               insecure=cmd_args.insecure,
                               is_debug=cmd_args.debug)
    _ = redfish_api.check_api_version()

    if cmd_args.verbose:
        logger.info("verbose is set on")

    if cmd_args.subcommand not in command_name_to_cmd:
        console_error_printer("Error: Unknown command.")
        return

    try:
        cmd = command_name_to_cmd[cmd_args.subcommand]
        arg_dict = dict((k, v) for k, v
                        in vars(cmd_args).items() if k != "message_type")

        if cmd_args.verbose:
            json_printer(arg_dict, cmd_args, colorized=cmd_args.nocolor)

        # invoke cmd
        command_result = redfish_api.sync_invoke(
            cmd.type, cmd.name, **arg_dict)

        if command_result.error is not None:
            json_printer(command_result.data, cmd_args, colorized=cmd_args.nocolor)
            if isinstance(command_result.error, JsonHttpError):
                console_error_printer(command_result.error.json_error)
            return

        processed_data = process_respond(cmd_args, command_result)
        if json_printer:
            json_printer(processed_data, cmd_args, colorized=cmd_args.nocolor)
    except TaskIdUnavailable as tid:
        console_error_printer(f"Error: {tid}")
    except MissingResource as mr:
        console_error_printer(f"Error: {mr}")
    except InvalidJsonSpec as ijs:
        console_error_printer(f"Error: {ijs}")
    except ResourceNotFound as rnf:
        console_error_printer(f"Error: {rnf}")
    except InvalidArgument as ia:
        console_error_printer(f"Error: {ia}")
    except FailedDiscoverAction as fda:
        console_error_printer(f"Error: {fda}")
    except UnsupportedAction as ua:
        console_error_printer(f"Error:{ua}")
    except MissingMandatoryArguments as mmr:
        console_error_printer(f"Error:{mmr}")
    except FileNotFoundError as fne:
        console_error_printer(f"Error:{fne}")
    except UncommittedPendingChanges as upc:
        console_error_printer(f"Error:{upc}")


def create_cmd_tree(arg_parser, debug=False) -> Dict:
    """Create command tree structure.
    :return: a dict that store mapping for each command.
    """
    redfish_api = IDracManager()
    command_name_to_cmd = {}
    commands_registry = redfish_api.get_registry()
    command_name = collections.namedtuple("Command", "type name")

    subparsers = arg_parser.add_subparsers(
        title='main command',
        metavar="main command",
        help='list of idrac_ctl commands',
        dest="subcommand",
        description='''Each action requires choosing 
        a main command bios, boot, etc|n          
        Example: idrac_ctl bios\n''',
        required=True
    )

    for k in commands_registry:
        for sub_key in commands_registry[k]:
            cls = commands_registry[k][sub_key]
            if debug:
                logger.debug(f"Registering command {k} {sub_key}")
            if hasattr(cls, "register_subcommand"):
                # register each command
                cli_arg_parser, cmd_name, cmd_help = cls.register_subcommand(cls)
                if debug:
                    logger.debug(f"Registering command name {cmd_name} {cmd_help}")

                subparsers.add_parser(
                    cmd_name,
                    parents=[cli_arg_parser],
                    help=f"{str(cmd_help)}",
                    formatter_class=CustomArgumentDefaultsHelpFormatter,
                )
                command_name_to_cmd[cmd_name] = command_name(k, sub_key)

    return command_name_to_cmd


def idrac_main_ctl():
    """
    """
    logger.setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(prog="idrac_ctl", add_help=True,
                                     description='''iDrac command line tools. |n
                                     It a standalone command line tool provide option to interact with  |n 
                                     Dell iDRAC via Redfish REST API. It supports both asynchronous and |n
                                     synchronous options to interact with iDRAC.|n
                                     Author Mus''',
                                     epilog='''For more detail, for example, documentation. Make sure to check.
                                             https://github.com/spyroot/idrac_ctl |n
                                             The example folder container many examples.
                                             Author Mustafa Bayramov spyroot@gmail.com
                                             ''',
                                     formatter_class=CustomArgumentDefaultsHelpFormatter)

    credentials = parser.add_argument_group('credentials', '# idrac credentials details.')

    # global args
    credentials.add_argument(
        '--idrac_ip', required=False, type=str,
        default=os.environ.get('IDRAC_IP', ''),
        help="idrac ip address, by default "
             "read from environment IDRAC_IP.")
    credentials.add_argument(
        '--idrac_username', required=False, type=str,
        default=os.environ.get('IDRAC_USERNAME', 'root'),
        help="idrac ip address, by default "
             "read from environment IDRAC_USERNAME.")
    credentials.add_argument(
        '--idrac_password', required=False, type=str,
        default=os.environ.get('IDRAC_PASSWORD', ''),
        help="idrac ip address, by default "
             "read from environment IDRAC_PASSWORD.")
    credentials.add_argument(
        '--insecure', action='store_true', required=False,
        help="insecure ssl.")

    verbose_group = parser.add_argument_group('verbose', '# verbose and debug options')
    verbose_group.add_argument(
        '--debug', action='store_true', required=False,
        help="enables debug.")
    verbose_group.add_argument(
        '--verbose', action='store_true', required=False, default=False,
        help="enables verbose output.")

    # controls for output
    output_controllers = parser.add_argument_group('output', '# output controller options')
    output_controllers.add_argument(
        '--no_extra', action='store_true', required=False, default=False,
        help="disables extra data stdout output.")
    output_controllers.add_argument(
        '--no_action', action='store_true', required=False, default=False,
        help="disables rest action data stdout output.")
    output_controllers.add_argument(
        '--json', action='store_true', required=False, default=True,
        help="by default we use json to output to console.")
    output_controllers.add_argument(
        '--json_only', action='store_true', required=False, default=False,
        help="by default output has different section. "
             "--json_only will merge all in one single output.")
    output_controllers.add_argument(
        '-d', '--data_only', action='store_true', required=False, default=False,
        help="for commands where we only need single value from json.")
    output_controllers.add_argument(
        '--no-stdout', '--no_stdout', action='store_true', required=False, default=False,
        help="by default we use stdout output.")
    output_controllers.add_argument(
        '--nocolor', action='store_false', required=False, default=True,
        help="by default output to terminal is colorful.")

    output_controllers.add_argument(
        '-f', '--filename', required=False, type=str,
        default="", help="Filename if we need save to a file.")
    parser.add_argument('-v', '--version', action='version',
                        version="%(prog)s " + __version__)

    cmd_dict = create_cmd_tree(parser)
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.idrac_ip is None or len(args.idrac_ip) == 0:
        print(
            "Please indicate the idrac ip. "
            "--idrac_ip or set IDRAC_IP environment variable. "
            "(export IDRAC_IP=ip_address)"
        )
        sys.exit(1)
    if args.idrac_username is None or len(args.idrac_username) == 0:
        print(
            "Please indicate the idrac username."
            "--idrac_username or set IDRAC_USERNAME environment variable. "
            "(export IDRAC_USERNAME=ip_address)"
        )
        sys.exit(1)
    if args.idrac_password is None or len(args.idrac_password) == 0:
        print(
            "Please indicate the idrac password. "
            "--idrac_password or set IDRAC_PASSWORD environment."
            "(export IDRAC_PASSWORD=ip_address)"
        )
        sys.exit(1)

    try:
        main(args, cmd_dict)
    except AuthenticationFailed as af:
        console_error_printer(f"Error: {af}")
    except requests.exceptions.ConnectionError as http_error:
        console_error_printer(f"Error: {http_error}")
    except ssl.SSLCertVerificationError as ssl_err:
        console_error_printer(f"Error: {ssl_err}")


