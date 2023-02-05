"""Main entry for idrac_ctl

The main interface consumed is iDRAC Manager class.
Each command registered dynamically and dispatch to respected execute method
by invoking request from IDRAC Manager.

Author Mus spyroot@gmail.com
"""

import argparse
import collections
import json
import os
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
from idrac_ctl.cmd_exceptions import InvalidArgument, FailedDiscoverAction, \
    UnsupportedAction, AuthenticationFailed, ResourceNotFound
from idrac_ctl.idrac_manager import IDracManager
from idrac_ctl.custom_argparser.customer_argdefault import CustomArgumentDefaultsHelpFormatter

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


def formatter(prog):
    argparse.HelpFormatter(prog, max_help_position=100, width=200)


class info:
    version = '1.0.5'
    description = 'iDRAC command line tools.'
    author = 'Mus'
    author_email = 'spyroot@gmail.com'


__version__ = info.version


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
            json_raw = json.dumps(json.loads(json_data),
                                  sort_keys=sort, indent=indents)
        else:
            json_raw = json.dumps(json_data,
                                  sort_keys=sort, indent=indents,
                                  cls=RedfishActionEncoder)

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


def main(cmd_args: argparse.Namespace, command_name_to_cmd: Dict) -> None:
    """Main entry point
    """
    if cmd_args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    redfish_api = IDracManager(idrac_ip=cmd_args.idrac_ip,
                               idrac_username=cmd_args.idrac_username,
                               idrac_password=cmd_args.idrac_password,
                               insecure=cmd_args.insecure,
                               is_debug=cmd_args.debug)

    _ = redfish_api.check_api_version()

    if cmd_args.verbose:
        print("Verbose is set on")

    try:
        if cmd_args.subcommand in command_name_to_cmd:
            cmd = command_name_to_cmd[cmd_args.subcommand]
            arg_dict = dict((k, v) for k, v in vars(cmd_args).items() if k != "message_type")
            if cmd_args.verbose:
                print("# args dictionary:")
                json_printer(arg_dict, cmd_args)

            command_result = redfish_api.sync_invoke(cmd.type,
                                                     cmd.name,
                                                     **arg_dict)

            if cmd_args.json and command_result.data is not None:
                json_printer(command_result.data, cmd_args,
                             header="# respond data from the command:")

            # extra data for deep walks
            if command_result.extra is not None and cmd_args.no_extra is False:
                extra = command_result.extra
                if cmd_args.json:
                    json_printer(extra, cmd_args,
                                 header="#command extra data:")

                # save extra as separate files.
                if hasattr(cmd_args, 'do_save') and cmd_args.do_save:
                    for extra_k in extra.keys():
                        if cmd_args.verbose:
                            print(f"Saving {extra_k}.json")
                        save_if_needed(f"{extra_k}.json", extra[extra_k])

            # discovered rest action.
            if command_result.discovered is not None and cmd_args.no_action is False:
                if cmd_args.json:
                    if isinstance(command_result.discovered, dict):
                        for ak in command_result.discovered.keys():
                            if isinstance(command_result.discovered[ak], RedfishAction):
                                json_printer(json.dumps(command_result.discovered[ak].__dict__), cmd_args,
                                             header="# Redfish actions:")
                            else:
                                json_printer(json.dumps(command_result.discovered[ak]),
                                             cmd_args,
                                             header="# Redfish actions:")
                    else:
                        json_printer(command_result.discovered, cmd_args,
                                     header="# Redfish actions:")

    except ResourceNotFound as rnf:
        print("Error:", rnf)
    except InvalidArgument as ia:
        print("Error:", ia)
    except FailedDiscoverAction as fda:
        print("Error:", fda)
    except UnsupportedAction as ua:
        print("Error:", ua)


def create_cmd_tree(arg_parser, debug=False) -> Dict:
    """Create command tree structure.
    :return:
    """
    redfish_api = IDracManager()
    command_name_to_cmd = {}
    commands_registry = redfish_api.get_registry()
    command_name = collections.namedtuple("Command", "type name")

    subparsers = arg_parser.add_subparsers(title='main command', metavar="main command",
                                           help='list of idrac_ctl commands',
                                           dest="subcommand",
                                           description='''Each action requires choosing
                                           a main command bios, boot, etc|n          
                                           Example: idrac_ctl.py bios\n''',
                                           required=True)

    for k in commands_registry:
        for sub_key in commands_registry[k]:
            cls = commands_registry[k][sub_key]
            if debug:
                print(f"Registering command {k} {sub_key}")
            if hasattr(cls, "register_subcommand"):
                cli_arg_parser, cmd_name, cmd_help = cls.register_subcommand(cls)
                if debug:
                    print(f"Registering command name {cmd_name} {cmd_help}")
                subparsers.add_parser(cmd_name, parents=[cli_arg_parser], help=f"{str(cmd_help)}",
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
                                     epilog="For more details example. Make sure to check."
                                            "https://github.com/spyroot/idrac_ctl",
                                     formatter_class=CustomArgumentDefaultsHelpFormatter)
    # global args
    parser.add_argument('--idrac_ip', required=False, type=str,
                        default=os.environ.get('IDRAC_IP', ''),
                        help="idrac ip address, by default "
                             "read from environment IDRAC_IP.")
    parser.add_argument('--idrac_username', required=False, type=str,
                        default=os.environ.get('IDRAC_USERNAME', 'root'),
                        help="idrac ip address, by default "
                             "read from environment IDRAC_USERNAME.")
    parser.add_argument('--idrac_password', required=False, type=str,
                        default=os.environ.get('IDRAC_PASSWORD', ''),
                        help="idrac ip address, by default "
                             "read from environment IDRAC_PASSWORD.")
    parser.add_argument('--insecure', action='store_true', required=False,
                        help="insecure ssl.")
    parser.add_argument('--debug', action='store_true', required=False,
                        help="enables debug.")
    parser.add_argument('--verbose', action='store_true', required=False, default=False,
                        help="enables verbose output.")
    parser.add_argument('--no_extra', action='store_true', required=False, default=False,
                        help="disables extra data stdout output.")
    parser.add_argument('--no_action', action='store_true', required=False, default=False,
                        help="disables rest action data stdout output.")
    parser.add_argument('--json', action='store_true', required=False, default=True,
                        help="by default we use json to output to console.")
    parser.add_argument('--json_only', action='store_true', required=False, default=False,
                        help="by default we use different section. --json_only will output only json.")
    parser.add_argument('--no-stdout', '--no_stdout', action='store_true', required=False, default=False,
                        help="by default we use stdout output.")
    parser.add_argument('-f', '--filename', required=False, type=str,
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
            "(export IDRAC_IP=ip_address"
        )
        sys.exit(1)
    if args.idrac_username is None or len(args.idrac_username) == 0:
        print(
            "Please indicate the idrac username."
            "--idrac_username or set IDRAC_USERNAME environment variable. "
            "(export IDRAC_USERNAME=ip_address"
        )
        sys.exit(1)
    if args.idrac_password is None or len(args.idrac_password) == 0:
        print(
            "Please indicate the idrac password. "
            "--idrac_password or set IDRAC_PASSWORD environment."
            "(export IDRAC_PASSWORD=ip_address"
        )
        sys.exit(1)

    try:
        main(args, cmd_dict)
    except AuthenticationFailed as af:
        print(f"Error: {af}")
    except requests.exceptions.ConnectionError as http_error:
        print(f"Error: {http_error}")



