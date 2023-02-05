"""iDRAC IDracManager

idrac_ctl interacts with iDRAC via REST API interface.

Main class command line tools utilizes. Each command must inherit
from this class. The class itself provides a register pattern where
each sub-command is registered automatically.
During the module phase, each sub-command is discovered and loaded,
allowing anyone to extend and add their own set of subcommands easily.

- The interaction with iDRAC done via REST API.
- Each command must provide option invoke command synchronously
  or asynchronously

Each command return CommandResult named tuple where data
is actually data returned from rest API response.

CommandResult.discovered hold all rest endpoint.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import collections
import functools

import requests
import json
import time
from tqdm import tqdm
from abc import abstractmethod
from typing import Optional, Tuple, Dict, Any
import re
import logging

from idrac_ctl.shared import ApiRequestType, RedfishAction, ScheduleJobType
from idrac_ctl.cmd_utils import save_if_needed
from .cmd_exceptions import AuthenticationFailed
from .cmd_exceptions import PostRequestFailed
from .cmd_exceptions import MissingResource
from .cmd_exceptions import UnexpectedResponse
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import PatchRequestFailed
from .cmd_exceptions import DeleteRequestFailed
from .cmd_exceptions import UnsupportedAction

"""Each command encapsulate result in named tuple"""
CommandResult = collections.namedtuple("cmd_result",
                                       ("data", "discovered", "extra"))

module_logger = logging.getLogger('idrac_ctl.idrac_manager')


class IDracManager:
    """
    Main Class, that interact with iDRAC via REST API interface.
    """
    _registry = {t: {} for t in ApiRequestType}

    def __init__(self, idrac_ip: Optional[str] = "",
                 idrac_username: Optional[str] = "root",
                 idrac_password: Optional[str] = "",
                 insecure: Optional[bool] = False,
                 x_auth: Optional[str] = None,
                 is_debug: Optional[bool] = False):
        """Default constructor for idrac requires credentials.
           By default, iDRAC Manager uses json to serialize a data to callee
           and uses json content type.

        :param idrac_ip: idrac mgmt IP address
        :param idrac_username: idrac username default is root
        :param idrac_password: idrac password.
        :param insecure: by default, we use insecure SSL
        :param x_auth: X-Authentication header.
        """
        self._idrac_ip = idrac_ip
        self._username = idrac_username
        self._password = idrac_password
        self._is_verify_cert = insecure
        self._x_auth = x_auth
        self._is_debug = is_debug

        self.logger = logging.getLogger(__name__)

        self.content_type = {'Content-Type': 'application/json; charset=utf-8'}
        self.json_content_type = {'Content-Type': 'application/json; charset=utf-8'}

        # run time
        self.action_targets = None
        self.api_endpoints = None
        self._post_success_responses = [200, 201, 202, 203, 204]
        self._patch_success_responses = [200, 201, 202, 203, 204]
        self._delete_success_responses = [200, 201, 202, 203, 204]

    @property
    def idrac_ip(self):
        return self._idrac_ip

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def x_auth(self):
        return self._x_auth

    def __init_subclass__(cls, scm_type=None, name=None, **kwargs):
        """Initialize and register all sub-commands.
        :param scm_type:
        :param name: sub-command name to differentiate each subcommand
        :param kwargs:
        :return:
        """
        super().__init_subclass__(**kwargs)
        if scm_type is not None:
            cls._registry[scm_type][name] = cls

    @abstractmethod
    def execute(self, **kwargs) -> CommandResult:
        """Each sub-command must implement this method.  A dispatch automatically will
        dispatch to each command, each command discovered during initial phase."""
        pass

    @staticmethod
    @abstractmethod
    def register_subcommand(cls) -> Tuple[argparse.ArgumentParser, str, str]:
        """Each sub-command registers itself. Each command has its
        own set of arguments and optional arguments.
        :return: a Tuple that hold ArgumentParser, command name str, command help str
        """
        pass

    @classmethod
    def get_registry(cls):
        """Return current command registry.
        :return:
        """
        return dict(cls._registry)

    @classmethod
    def invoke(cls,
               api_call: ApiRequestType,
               name: str, **kwargs) -> CommandResult:
        """Main interface uses to invoke a command.
        :param api_call: api request type is enum for each cmd.
        :param name: a name is key for a given api request type.
                      So we can register under same type sub-commands.
        :param kwargs: args passed to command.
        :return:
        """
        z = cls._registry[api_call]
        if name not in z:
            raise UnsupportedAction(f"Unknown {name} command.")
        disp = z[name]
        _idrac_ip = kwargs.pop("idrac_ip")
        _username = kwargs.pop("username")
        _password = kwargs.pop("password")

        inst = disp(
            idrac_ip=_idrac_ip,
            idrac_username=_username,
            idrac_password=_password
        )
        return inst.execute(**kwargs)

    async def async_invoke(cls, api_call: ApiRequestType, name: str, **kwargs) -> CommandResult:
        """Main interface uses to invoke a command.
        :param api_call: api request type is enum for each cmd.
        :param name:
        :param kwargs:
        :return:
        """
        z = cls._registry[api_call]
        disp = z[name]
        if name not in z:
            raise UnsupportedAction(f"Unknown {name} command.")
        _idrac_ip = kwargs.pop("idrac_ip")
        _username = kwargs.pop("username")
        _password = kwargs.pop("password")

        inst = disp(
            idrac_ip=_idrac_ip,
            idrac_username=_username,
            idrac_password=_password
        )
        return inst.execute(**kwargs)

    async def api_async_get_call(self, loop, r, hdr: Dict):
        """Make api request either with x-auth authentication header or idrac_ctl.
        :param loop:  asyncio event loop
        :param r:  request
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            return loop.run_in_executor(
                None, functools.partial(requests.get, r,
                                        verify=self._is_verify_cert,
                                        headers=headers)
            )
        else:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.get, r,
                    verify=self._is_verify_cert,
                    auth=(self._username, self._password)
                )
            )

    async def api_async_get_until_complete(self, r, hdr: Dict, loop=None):
        """
        :param r:
        :param hdr:
        :param loop:
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_get_call(loop, r, hdr)
        await self.async_default_error_handler(await response)
        return await response

    def api_get_call(self,
                     r: str,
                     hdr: Dict) -> requests.models.Response:
        """Make api request either with x-auth authentication header or idrac_ctl.
        :param r:  request
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            headers.update({'X-Auth-Token': self.x_auth})
            return requests.get(
                r, verify=self._is_verify_cert, headers=headers
            )
        else:
            return requests.get(
                r, verify=self._is_verify_cert,
                auth=(self._username, self._password)
            )

    def api_delete_call(self, r, hdr: Dict):
        """Make api request for delete method.
        :param r:  request
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            headers.update({'X-Auth-Token': self.x_auth})
            return requests.delete(r,
                                   verify=self._is_verify_cert,
                                   headers=headers
                                   )
        else:
            return requests.delete(
                r, verify=self._is_verify_cert,
                auth=(self._username, self._password),
                headers=headers
            )

    def sync_invoke(self, api_call: ApiRequestType, name: str, **kwargs) -> CommandResult:
        """Synchronous invocation of target command
        :param api_call: A enum for command.
        :param name: A name for command to differentiate sub-commands.
        :param kwargs: Args passed to a command.
        :return: Return result depends on actual command.
        """
        kwargs.update(
            {
                "idrac_ip": self._idrac_ip,
                "username": self._username,
                "password": self._password
            }
        )
        return self.invoke(api_call, name, **kwargs)

    def fetch_job(self,
                  job_id: str,
                  sleep_time: Optional[int] = 2,
                  wait_for: Optional[int] = 200):
        """synchronous fetch a job from iDRAC and wait for completion.
        :param wait_for:  by default, we wait status code 200 based on spec.
        :param job_id: job id as it returned from a task by idrac
        :param sleep_time: sleep and wait.
        :return: Nothing
        :raise AuthenticationFailed MissingResource
        """
        last_update = 0
        percent_done = 0
        with tqdm(total=100) as pbar:
            while True:
                resp = self.api_get_call(f"https://{self.idrac_ip}/redfish/v1/"
                                         f"TaskService/Tasks/{job_id}", hdr={})
                if resp.status_code == 401:
                    AuthenticationFailed("Authentication failed.")
                elif resp.status_code == 404:
                    raise MissingResource("Missing resource.")
                elif resp.status_code == wait_for:
                    resp_data = resp.json()
                    return resp_data
                elif resp.status_code == 202:
                    resp_data = resp.json()
                    if 'TaskStatus' in resp_data and resp_data['TaskStatus'] == 'OK':
                        if 'PercentComplete' in resp_data:
                            try:
                                percent_done = int(resp_data['PercentComplete'])
                            except TypeError:
                                pass
                            if percent_done > last_update:
                                last_update = percent_done
                                inc = percent_done - pbar.n
                                pbar.update(n=inc)
                            time.sleep(sleep_time)
                else:
                    self.logger.error("unexpected status code", resp.status_code)
                    time.sleep(sleep_time)

        return resp_data

    @staticmethod
    async def async_default_error_handler(response: requests.models.Response) -> bool:
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code >= 200 or response.status_code < 300:
            return True
        if response.status_code == 401:
            raise AuthenticationFailed(
                "Authentication failed."
            )
        if response.status_code != 200:
            raise UnexpectedResponse(
                f"Failed acquire result. "
                f"Status code {response.status_code}"
            )

    @staticmethod
    def default_error_handler(response) -> bool:
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code >= 200 or response.status_code < 300:
            return True
        if response.status_code == 401:
            raise AuthenticationFailed("Authentication failed.")
        if response.status_code == 404:
            error_msg = IDracManager.parse_error(response)
            raise ResourceNotFound(error_msg)
        if response.status_code != 200:
            raise UnexpectedResponse(f"Failed acquire result. Status code {response.status_code}")

    def check_api_version(self):
        """Check Dell LLC Service API set
        :return:
        """
        headers = {}
        headers.update(self.json_content_type)
        r = f"https://{self._idrac_ip}/redfish/v1/Dell/Managers" \
            f"/iDRAC.Embedded.1/DellLCService"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)

        data = response.json()
        self.api_endpoints = data
        if 'Actions' in self.api_endpoints:
            actions = self.api_endpoints["Actions"]
            action_keys = actions.keys()
            self.action_targets = [actions[k]['target'] for k in action_keys]

        return self.api_endpoints, self.action_targets

    @staticmethod
    @abstractmethod
    def default_json_printer(json_data,
                             sort: Optional[bool] = True,
                             indents: Optional[int] = 4):
        """json default stdout printer.
        :param json_data:
        :param indents:
        :param sort:
        :return:
        """
        if isinstance(json_data, requests.models.Response):
            json_data = json_data.json()

        if isinstance(json_data, str):
            json_raw = json.dumps(
                json.loads(json_data), sort_keys=sort, indent=indents
            )
        else:
            json_raw = json.dumps(
                json_data, sort_keys=sort, indent=indents
            )
        print(json_raw)

    @staticmethod
    def _get_actions(cls, json_data):
        """Parse json iDRAC Manager for all supported action
        and action method arg.
        :param cls:
        :param json_data:
        :return:
        """
        unfiltered_actions = {}
        full_redfish_names = {}

        if 'Actions' not in json_data:
            return unfiltered_actions, full_redfish_names

        redfish_actions = json_data['Actions']
        for a in redfish_actions:
            _ca = redfish_actions[a]
            if a == "Oem" and isinstance(_ca, dict):
                for k in _ca.keys():
                    rest_api_action = k.split(".")
                    if len(rest_api_action) < 2:
                        continue
                    rest_api_action = rest_api_action[-1]
                    unfiltered_actions[rest_api_action] = _ca[k]
                    full_redfish_names[rest_api_action] = k
            else:
                rest_api_action = a.split(".")
                if len(rest_api_action) < 2:
                    continue
                rest_api_action = rest_api_action[-1]
                unfiltered_actions[rest_api_action] = _ca
                full_redfish_names[rest_api_action] = a

        return unfiltered_actions, full_redfish_names

    @staticmethod
    def discover_member_redfish_actions(cls, json_data):
        """
        :param cls:
        :param json_data:
        :return:
        """
        action_dict = {}
        if 'Members' not in json_data:
            if 'Actions' in json_data:
                return cls.discover_redfish_actions(cls, json_data)
            else:
                return action_dict

        member_data = json_data['Members']
        for m in member_data:
            if isinstance(m, dict):
                if 'Actions' in m.keys():
                    action = cls.discover_redfish_actions(cls, m)
                    action_dict.update(action)

        return action_dict

    @staticmethod
    def discover_redfish_actions(cls, json_data):
        """Discovers all redfish action, args and args choices.
        :param cls:
        :param json_data:
        :return:
        """
        if isinstance(json_data, requests.models.Response):
            json_data = json_data.json()

        action_dict = {}
        unfiltered_actions, full_redfish_names = cls._get_actions(cls, json_data)
        for ra in unfiltered_actions.keys():
            if 'target' not in unfiltered_actions[ra]:
                continue
            action_tuple = unfiltered_actions[ra]
            if isinstance(action_tuple, Dict):
                arg_keys = action_tuple.keys()
                redfish_action = RedfishAction(action_name=ra,
                                               target=action_tuple['target'],
                                               full_redfish_name=full_redfish_names[ra])
                action_dict[ra] = redfish_action
                for k in arg_keys:
                    if '@Redfish.AllowableValues' in k:
                        arg_name = k.split('@')[0]
                        action_dict[ra].add_action_arg(arg_name, action_tuple[k])

        return action_dict

    def version_api(self, data_type: Optional[str] = "json") -> bool:
        """Return true if a new version.
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)
        r = f"https://{self.idrac_ip}/redfish/v1/Managers" \
            f"/iDRAC.Embedded.1?$select=FirmwareVersion"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        return int(data["FirmwareVersion"].replace(".", "")) >= 6000000

    @staticmethod
    def filter_attribute(cls, json_data, attr_filter: Optional[str]):
        """Filter attribute from json_data
        :param cls:
        :param json_data:
        :param attr_filter:
        :return:
        """
        if attr_filter is not None and len(attr_filter) > 0 and 'Attributes' in json_data:
            attr_filter = attr_filter.strip()
            if "," in attr_filter:
                attr_filters = attr_filter.split(",")
                if len(attr_filters) > 0:
                    json_data = dict((a, json_data['Attributes'][attr])
                                     for attr in json_data['Attributes'] for a in attr_filters
                                     if a.lower() in attr.lower())
            else:
                json_data = dict((attr, json_data['Attributes'][attr])
                                 for attr in json_data['Attributes']
                                 if attr_filter.lower() in attr.lower())
        return json_data

    def api_post_call(self,
                      req: str,
                      payload: str,
                      hdr: dict) -> requests.models.Response:
        """Make api post request.
        :param req: path to a path request
        :param payload:  json payload
        :param hdr: header that will append.
        :return: response.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            headers.update({'X-Auth-Token': self.x_auth})
            return requests.post(
                req,
                data=payload,
                verify=self._is_verify_cert,
                headers=headers
            )
        else:
            return requests.post(
                req, data=payload,
                verify=self._is_verify_cert,
                headers=headers,
                auth=(self._username, self._password)
            )

    async def api_async_post_call(self, loop, req: str, payload: str, hdr: Dict):
        """Make post api request either with x-auth authentication header or idrac_ctl.
        :param loop:  asyncio event loop
        :param req:  request
        :param payload:  json payload
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.post, req,
                    data=payload,
                    verify=self._is_verify_cert,
                    headers=headers
                )
            )
        else:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.post, req,
                    data=payload,
                    headers=headers,
                    verify=self._is_verify_cert,
                    auth=(self._username, self._password)
                )
            )

    async def api_async_patch_until_complete(
            self, r: str,
            payload: str,
            hdr: Dict, loop=None) -> Tuple[requests.models.Response, bool]:
        """Make async patch api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param r: request.
        :param hdr: http header.
        :param loop: asyncio loop
        :param payload: json payload
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_patch_call(loop, r, payload, hdr)
        ok = await self.async_default_patch_success(await response)
        return await response, ok

    async def async_post_until_complete(
            self, r: str,
            payload: str,
            hdr: Dict,
            loop=None) -> Tuple[requests.models.Response, bool]:
        """Make async post api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param r: request.
        :param hdr: http header.
        :param loop: asyncio loop
        :param payload: json payload
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_post_call(loop, r, payload, hdr)
        ok = await self.async_default_post_success(await response)
        return await response, ok

    def api_patch_call(self,
                       req: str,
                       payload: str,
                       hdr: dict) -> requests.models.Response:
        """Make api patch request.
        :param req: path to a path request
        :param payload: json payload
        :param hdr: header that will append.
        :return: response.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            headers.update({'X-Auth-Token': self.x_auth})
            return requests.patch(req,
                                  data=payload,
                                  verify=self._is_verify_cert,
                                  headers=headers)
        else:
            return requests.patch(req,
                                  data=payload,
                                  verify=self._is_verify_cert,
                                  headers=headers,
                                  auth=(self._username, self._password))

    async def api_async_patch_call(self, loop, req, payload: str, hdr: Dict):
        """Make async post api request either with
        x-auth authentication header or idrac_ctl.

        :param loop:  asyncio event loop
        :param req:  request
        :param payload:  json payload
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            return loop.run_in_executor(
                None, functools.partial(requests.patch, req,
                                        data=payload,
                                        verify=self._is_verify_cert,
                                        headers=headers)
            )
        else:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.patch, req, data=payload,
                    verify=self._is_verify_cert, headers=headers,
                    auth=(self._username, self._password)
                )
            )

    async def api_async_delete_call(self, loop,
                                    req, payload: str, hdr: Dict):
        """Make async delete api request either with
        x-auth authentication header or idrac_ctl.

        :param loop:  asyncio event loop
        :param req:  request
        :param payload:  json payload
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.delete, req, data=payload,
                    verify=self._is_verify_cert,
                    headers=headers)
            )
        else:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.delete, req, data=payload,
                    verify=self._is_verify_cert,
                    headers=headers,
                    auth=(self._username, self._password)
                )
            )

    @staticmethod
    def parse_error(error_response: requests.models.Response):
        """Default Parser for error msg from
        JSON error response based on iDRAC.
        :param error_response:
        :return:
        """
        err_msg = "Default error."
        err_resp = error_response.json()
        if 'error' in err_resp:
            err_data = err_resp['error']
            if 'message' in err_data:
                err_msg = err_resp['error']['message']
            if '@Message.ExtendedInfo' in err_data:
                extended_err = err_data['@Message.ExtendedInfo'][-1]
                err_msg = [f"{k}: {v}" for k, v in extended_err.items() if "@" not in k]
                err_msg = "\n".join(err_msg)

        return err_msg

    @staticmethod
    def default_patch_success(cls,
                              response: requests.models.Response,
                              expected: Optional[int] = 200) -> bool:
        """Default HTTP patch success handler
        Default handler to check patch request respond.

        :param cls:
        :param response: HTTP response
        :param expected:  Option status code that we caller consider success.
        :return: True if patch msg succeed
        :raise PatchFailed if patch failed
        """
        if response.status_code == expected:
            return True

        if response.status_code == 200 \
                or response.status_code == 202 or response.status_code == 204:
            return True
        else:
            err_msg = IDracManager.parse_error(response)
            raise PatchRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}"
            )

    @staticmethod
    def default_post_success(cls,
                             response: requests.models.Response,
                             expected: Optional[int] = 204) -> bool:
        """Default post success handler,  Check for status code.
        and raise exception.  Default handler to check post
        request respond.

        :param cls:
        :param response: HTTP response
        :param expected:  Option status code that we caller consider success.
        :return: True if patch msg succeed
        :raise PostRequestFailed if POST Method failed
        """
        if response.status_code == expected:
            return True

        if response.status_code == 200 \
                or response.status_code == 202 \
                or response.status_code == 204:
            return True
        else:
            err_msg = IDracManager.parse_error(response)
            raise PostRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}"
            )

    @staticmethod
    def default_delete_success(response: requests.models.Response,
                               expected: Optional[int] = 200) -> bool:
        """Default delete success handler,  Check for status code.
        and raise exception.  Default handler to check post
        request respond.

        :param response: HTTP response
        :param expected:  Option status code that we caller consider success.
        :return: True if patch msg succeed
        :raise DeleteRequestFailed if POST Method failed
        """
        if response.status_code == expected:
            return True

        if response.status_code == 200 \
                or response.status_code == 202 \
                or response.status_code == 204:
            return True
        else:
            err_msg = IDracManager.parse_error(response)
            raise DeleteRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}"
            )

    def api_async_del_until_complete(self, r, headers):
        pass

    @staticmethod
    async def async_default_post_success(response: requests.models.Response) -> bool:
        """Default error handler, for post
        :param response: response HTTP response.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return IDracManager.default_post_success(IDracManager, response)

    @staticmethod
    async def async_default_delete_success(response: requests.models.Response) -> bool:
        """Default error handler, for post
        :param response: response HTTP response.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return IDracManager.default_delete_success(response)

    @staticmethod
    async def async_default_patch_success(response: requests.models.Response) -> bool:
        """Default error handler for patch http method.
        :param response: response HTTP response.
        :return: True or False and if failed raise exception
        """
        return IDracManager.default_patch_success(IDracManager, response)

    @staticmethod
    def expanded(level=1):
        """Return prefix to use for expanded respond.
        :param level:
        :return:
        """
        return f"?$expand=*($levels={level})"

    def base_query(self,
                   resource: str,
                   filename: Optional[str] = None,
                   do_async: Optional[bool] = False,
                   do_expanded: Optional[bool] = False,
                   data_type: Optional[str] = "json",
                   verbose: Optional[bool] = False,
                   key: Optional[str] = None,
                   **kwargs) -> CommandResult:
        """command will give the status of the Drivers and ISO Image
        that has been exposed to host.

        :param resource: path to a resource
        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :param key: Optional json key
        :return: CommandResult and if filename provide will save to a file.
        """
        if verbose:
            self.logger.info(
                f"cmd args"
                f"data_type: {data_type} "
                f"resource:{resource} "
                f"do_async:{do_async} "
                f"filename:{filename}")
            self.logger.info(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        if do_expanded:
            r = f"https://{self.idrac_ip}{resource}{self.expanded()}"
        else:
            r = f"https://{self.idrac_ip}{resource}"

        if not do_async:
            response = self.api_get_call(r, headers)
            self.default_error_handler(response)
        else:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self.api_async_get_until_complete(
                    r, headers
                )
            )

        data = response.json()
        if key is not None and len(key) > 0 and key in data:
            data = data[key]

        save_if_needed(filename, data)
        return CommandResult(data, None, None)

    def base_patch(self,
                   resource: str,
                   payload: Optional[dict] = None,
                   do_async: Optional[bool] = False,
                   data_type: Optional[str] = "json",
                   expected_status: Optional[int] = 200) -> CommandResult:
        """Base http patch
        :param resource:
        :param payload:
        :param do_async:
        :param data_type:
        :param expected_status:
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        if payload is None:
            pd = {}
        else:
            pd = payload

        ok = False
        response = None
        try:
            r = f"https://{self.idrac_ip}{resource}"
            if not do_async:
                if self._is_debug:
                    self.logger.debug(json.dumps(pd))
                response = self.api_patch_call(
                    r, json.dumps(pd), headers
                )
                ok = self.default_patch_success(
                    self, response, expected=expected_status
                )
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(
                    self.api_async_patch_until_complete(
                        r, json.dumps(pd), headers
                    )
                )
        except PatchRequestFailed as pf:
            self.logger.critical(
                pf, exc_info=self._is_debug
            )
            pass

        return CommandResult(self.api_success_msg(ok), None, response)

    def base_post(self,
                  resource: str,
                  payload: Optional[dict] = None,
                  do_async: Optional[bool] = False,
                  data_type: Optional[str] = "json",
                  expected_status: Optional[int] = 20,
                  verbose: Optional[bool] = False) -> CommandResult:
        """Base http post request
        :param resource: a remote resource
        :param payload: a json payload
        :param do_async:
        :param data_type:
        :param expected_status:
        :param verbose: enables verbose output
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        if payload is None:
            pd = {}
        else:
            pd = payload

        ok = False
        response = None
        try:
            r = f"https://{self.idrac_ip}{resource}"
            if not do_async:
                response = self.api_post_call(r, json.dumps(pd), headers)
                if verbose:
                    print(f"received status code {response.status_code}")
                    print(f"received status code {response.headers}")
                    print(f"received {response.raw}")
                ok = self.default_post_success(
                    self, response, expected=expected_status
                )
            else:
                loop = asyncio.get_event_loop()
                ok, response = loop.run_until_complete(
                    self.async_post_until_complete(
                        r, json.dumps(pd), headers
                    )
                )
        except PostRequestFailed as pf:
            self.logger.critical(
                pf, exc_info=self._is_debug
            )

        return CommandResult(self.api_success_msg(ok), None, response)

    @staticmethod
    def api_success_msg(status: bool) -> Dict:
        """Default api success respond.
        :param status:
        :return:
        """
        return {"Status": status}

    def reboot(self,
               power_state_attr="PowerState",
               default_reboot_type="ForceRestart") -> dict:
        """Check if power state is on , reboots a host.
        :return: return a dict stora if operation succeed..
        """
        result_data = {}
        cmd_result = self.sync_invoke(
            ApiRequestType.ChassisQuery,
            "chassis_service_query",
            data_filter=power_state_attr
        )

        if isinstance(cmd_result.data, dict) and 'PowerState' in cmd_result.data:
            pd_state = cmd_result.data[power_state_attr]
            if pd_state == 'On':
                cmd_result = self.sync_invoke(
                    ApiRequestType.RebootHost, "reboot",
                    reset_type=default_reboot_type
                )
                if 'Status' in cmd_result.data:
                    result_data.update(
                        {
                            "Reboot": cmd_result.data['Status']
                        }
                    )
            else:
                self.logger.info(
                    f"Can't reboot a host, "
                    f"chassis power state in {pd_state} state."
                )
        else:
            self.logger.info(
                f"Failed to fetch chassis power state")

        return result_data

    def idrac_firmware(self):
        """Shared method return idrac firmware
        """
        return self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="FirmwareVersion")

    def idrac_last_reset(self):
        """Shared method return idrac last reset time"""
        return self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="LastResetTime")

    def idrac_current_time(self):
        """Shared method return idrac current time"""
        return self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="DateTime")

    def idrac_time_offset(self):
        """Shared method return idrac current time"""
        return self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="DateTimeLocalOffset")

    def idrac_manage_chassis(self):
        """Shared method return idrac managed chassis list as json"""
        links = self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="Links")
        if links.data is not None and 'ManagerForChassis' in links.data:
            return links.data['ManagerForChassis']
        return links

    def idrac_manage_servers(self):
        """Shared method return idrac managed servers list as json"""
        links = self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="Links")
        if links.data is not None and 'ManagerForServers' in links.data:
            return links.data['ManagerForServers']
        return links

    def idrac_id(self):
        """Shared method return idrac current time"""
        return self.base_query("/redfish/v1/Managers/iDRAC.Embedded.1", key="Id")

    @staticmethod
    def base_parser(is_async: Optional[bool] = True,
                    is_file_save: Optional[bool] = True,
                    is_expanded: Optional[bool] = True,
                    is_remote_share: Optional[bool] = False,
                    is_reboot: Optional[bool] = False):
        """This idrac_ctl optional parser for all sub command.
        Each sub-command can add additional optional flags
        and args.
        :return:
        """
        cmd_parser = argparse.ArgumentParser(add_help=False)
        if is_async:
            cmd_parser.add_argument(
                '-a', '--async', action='store_true',
                required=False, dest="do_async",
                default=False,
                help="will use async call."
            )

        if is_expanded:
            cmd_parser.add_argument(
                '-e', '--expanded', action='store_true',
                required=False, dest="do_expanded",
                default=False,
                help="expanded request for deeper view."
            )
        if is_file_save:
            cmd_parser.add_argument(
                '-f', '--filename', required=False, default="",
                type=str,
                help="filename if we need to save a respond to a file."
            )

        if is_reboot:
            cmd_parser.add_argument(
                '-r', '--reboot', action='store_true',
                required=False, dest="do_reboot",
                default=False,
                help="will reboot a host.")

        # this optional args for remote share CIFS/NFS/HTTP etc.
        if is_remote_share:
            cmd_parser.add_argument(
                '--ip_addr', required=True,
                type=str, default=None,
                help="ip address for CIFS|NFS."
            )
            cmd_parser.add_argument(
                '--share_type', required=False,
                type=str, default="CIFS",
                help="share type CIFS|NFS."
            )
            cmd_parser.add_argument(
                '--share_name', required=True,
                type=str, default=None,
                help="share name."
            )
            cmd_parser.add_argument(
                '--remote_image', required=True,
                type=str, default=None,
                help="remote image. Example my_iso. "
            )
            cmd_parser.add_argument(
                '--remote_username', required=False,
                type=str, default="vmware",
                help="remote username if required."
            )
            cmd_parser.add_argument(
                '--remote_password', required=False,
                type=str, default="123456",
                help="password if required."
            )
            cmd_parser.add_argument(
                '--remote_workgroup', required=False,
                type=str, default="",
                help="group name if required."
            )
        return cmd_parser

    @staticmethod
    def job_id_from_respond(
            response: requests.models.Response) -> Any | None:
        """Parses job id from a HTTP respond.
        :param response:
        :return:
        """
        try:
            if response is not None:
                response_dict = str(response.__dict__)
                if response_dict is not None and len(response_dict) > 0:
                    job_id = re.search("JID_.+?,", response_dict)
                    if job_id is not None:
                        job_id = job_id.group(0)
                    return job_id
        except AttributeError as _:
            pass

        return None

    @staticmethod
    def job_id_from_header(
            response: requests.models.Response) -> str:
        """Returns job id from the response header.
        :param response: a response that should have job
        id information in the header.
        :return: job id
        :raise UnexpectedResponse if header not present.
        """
        resp_hdr = response.headers
        if 'Location' not in resp_hdr:
            raise UnexpectedResponse(
                "There is no location in the response header. "
                "(not all api create job id)"
            )

        location = response.headers['Location']
        job_id = location.split("/")[-1]
        return job_id

    @staticmethod
    def schedule_job(
            reboot_type: ScheduleJobType,
            start_time: Optional[str],
            duration_time: Optional[int]) -> dict:
        """Schedule a job.
        :param reboot_type: reboot types.
        :param start_time: start time for a job
        :param duration_time: duration for a job
        :return:
        """
        if reboot_type == ScheduleJobType.NoReboot:
            pd = {
                "@Redfish.SettingsApplyTime": {
                    "ApplyTime": "InMaintenanceWindowOnReset",
                    "MaintenanceWindowStartTime": start_time,
                    "MaintenanceWindowDurationInSeconds": duration_time
                }
            }
        elif reboot_type == ScheduleJobType.AutoReboot:
            pd = {
                "@Redfish.SettingsApplyTime": {
                    "ApplyTime": "AtMaintenanceWindowStart",
                    "MaintenanceWindowStartTime": start_time,
                    "MaintenanceWindowDurationInSeconds": duration_time
                }
            }
        elif reboot_type == ScheduleJobType.OnReset:
            pd = {
                "@Redfish.SettingsApplyTime": {
                    "ApplyTime": "OnReset"
                }
            }
        elif reboot_type == ScheduleJobType.Immediate:
            pd = {
                "@Redfish.SettingsApplyTime": {
                    "ApplyTime": "Immediate"
                }
            }
        else:
            raise ValueError("Invalid settings apply time.")
        return pd

    def parse_task_id(self, data):
        """Parse input data and try to get job id from the header or response.
        :param data:
        :return:
        """
        # get response from extra
        if data is None:
            return {}

        if hasattr(data, "extra"):
            resp = data.extra
        elif isinstance(data, requests.models.Response):
            resp = data
        else:
            raise ValueError("Unknown data type.")

        if resp is None:
            return {}

        job_id = None
        try:
            job_id = self.job_id_from_header(resp)
            logging.debug(
                f"idrac api returned {job_id} in the header."
            )
            return job_id
        except UnexpectedResponse as ur:
            logging.debug(ur, exc_info=self._is_debug)

        try:
            # try to get from the response , it an optional check.
            if job_id is None:
                job_id = self.job_id_from_respond(resp)
                logging.debug(f"idrac api returned {job_id} in the header.")
        except UnexpectedResponse as _:
            pass

        if job_id is not None:
            data = self.fetch_job(job_id)
            return data

        return {}
