"""Main entry for idrac_ctl

The main interface consumed by ctl iDRAD Manager class.

Author Mus spyroot@gmail.com
"""

import argparse
import collections
import json
import os
import sys
from typing import Optional

import urllib3
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.data import JsonLexer

from base.idrac_manager import AuthenticationFailed, IDracManager, ResourceNotFound
from base.cmd_utils import save_if_needed
from base.shared import RedfishAction
from base.cmd_exceptions import InvalidArgument

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class info:
    version = '0.8'
    description = 'iDRAC command line tools.'
    author = 'Mus'
    author_email = 'spyroot@gmail.com'


__version__ = info.version


def json_printer(json_data, sort: Optional[bool] = True, indents: Optional[int] = 4,
                 colorized: Optional[bool] = True):
    """Json stdout printer.
    :param colorized:
    :param json_data:
    :param indents:
    :param sort:
    :return:
    """
    if isinstance(json_data, str):
        json_raw = json.dumps(json.loads(json_data), sort_keys=sort, indent=indents)
    else:
        json_raw = json.dumps(json_data, sort_keys=sort, indent=indents)

    if colorized:
        colorful = highlight(
                json_raw,
                lexer=JsonLexer(),
                formatter=Terminal256Formatter(),
        )
        print(colorful)
    else:
        print(json_raw)


def main(args):
    """
    Just do something
    """
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    redfish_api = IDracManager(idrac_ip=args.idrac_ip,
                               idrac_username=args.idrac_username,
                               idrac_password=args.idrac_password,
                               insecure=args.insecure)

    _ = redfish_api.check_api_version()

    if args.verbose:
        print("Verbose is on")

    try:
        if args.subcommand in command_name_to_cmd:
            cmd = command_name_to_cmd[args.subcommand]
            arg_dict = dict((k, v) for k, v in vars(args).items() if k != "message_type")
            print("#args dictionary:")
            if args.verbose:
                json_printer(arg_dict)

            command_result = redfish_api.sync_invoke(cmd.type,
                                                     cmd.name,
                                                     **arg_dict)

            if args.json and command_result.data is not None:
                print("#cmd respond:")
                json_printer(command_result.data)

            # extra data for deep walks
            if command_result.extra is not None:
                extra = command_result.extra
                print("#extra data:")
                if args.json:
                    json_printer(extra)

                # save extra as separate files.
                if hasattr(args, 'do_save') and args.do_save:
                    for extra_k in extra.keys():
                        if args.verbose:
                            print(f"Saving {extra_k}.json")
                        save_if_needed(f"{extra_k}.json", extra[extra_k])

            # discovered rest action.
            if command_result.discovered is not None:
                print("redfish actions:")
                if args.json:
                    if isinstance(command_result.discovered, dict):
                        for ak in command_result.discovered.keys():
                            if isinstance(command_result.discovered[ak], RedfishAction):
                                json_printer(json.dumps(command_result.discovered[ak].__dict__))
                            else:
                                json_printer(json.dumps(command_result.discovered[ak]))
                    else:
                        json_printer(command_result.discovered)

    except ResourceNotFound as rnf:
        print("Error:", rnf)
    except InvalidArgument as ia:
        print("Error:", ia)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=" iDrac command line tools. spyroot",
                                     epilog="For more details example. Make sure to check githib.")

    parser.add_argument('--idrac_ip', required=False, type=str,
                        default=os.environ.get('IDRAC_IP', ''),
                        help="idrac ip address, by default read from env IDRAC.")
    parser.add_argument('--idrac_username', required=False, type=str,
                        default=os.environ.get('IDRAC_USERNAME', 'root'),
                        help="idrac ip address, by default read from env IDRAC.")
    parser.add_argument('--idrac_password', required=False, type=str,
                        default=os.environ.get('IDRAC_PASSWORD', ''),
                        help="idrac ip address, by default read from env IDRAC.")
    parser.add_argument('--insecure', action='store_true', required=False,
                        help="insecure ssl.")
    parser.add_argument('--debug', action='store_true', required=False,
                        help="enables debug.")
    parser.add_argument('--verbose', action='store_true', required=False, default=False,
                        help="verbose output.")
    parser.add_argument('--json', action='store_true', required=False, default=True,
                        help="json console output.")
    parser.add_argument('-f', '--filename', required=False, type=str,
                        default="", help="Filename if we need save to a file.")

    subparsers = parser.add_subparsers(title='subcommand', help='system for subcommands', dest="subcommand")

    debug = False

    redfish_api = IDracManager()
    commands_registry = redfish_api.get_registry()
    command_name_to_cmd = {}
    command_name = collections.namedtuple("Command", "type name")

    for k in commands_registry:
        for sub_key in commands_registry[k]:
            cls = commands_registry[k][sub_key]
            if debug:
                print(f"Registering command {k} {sub_key}")
            if hasattr(cls, "register_subcommand"):
                arg_parser, cmd_name, cmd_help = cls.register_subcommand(cls)
                if debug:
                    print(f"Registering command name {cmd_name} {cmd_help}")
                subparsers.add_parser(cmd_name, parents=[arg_parser], help=f"{str(cmd_help)}")
                command_name_to_cmd[cmd_name] = command_name(k, sub_key)

    args = parser.parse_args()
    if args.idrac_ip is None or len(args.idrac_ip) == 0:
        print("Please indicate the idrac ip. --idrac_ip or set IDRACK_IP env.")
        sys.exit(1)
    if args.idrac_username is None or len(args.idrac_username) == 0:
        print("Please indicate the idrac username. --idrac_username or set IDRACK_USERNAME env.")
        sys.exit(1)
    if args.idrac_password is None or len(args.idrac_password) == 0:
        print("Please indicate the idrac password. --idrac_password or set IDRACK_PASSWORD env.")
        sys.exit(1)

    try:
        main(args)
    except AuthenticationFailed as af:
        print(f"Error: {af}")
