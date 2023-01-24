"""iDRAC IDracManager

idract_ctl interacts with iDRACT via REST API interface.

Main class command line tools utilizes.  Each command must inherit from this class.
The class itself provides a register pattern where each sub-command is registered automatically.
During the module phase, each sub-command is discovered and loaded, allowing anyone to extend
and add their own set of subcommands easily.

- The interaction with iDRAC done via REST API.
- Each command must provide option invoke command synchronously
  or asynchronously

Each command return CommandResult named tuple where data is actually data returned
from rest API response.

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
from typing import Optional, Tuple, Dict
from base.shared import ApiRequestType, RedfishAction

"""Each command encapsulate result in named tuple"""
CommandResult = collections.namedtuple("cmd_result",
                                       ("data", "discovered", "extra"))


class AuthenticationFailed(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class MissingResource(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class PatchFailed(Exception):
    pass


class PostFailed(Exception):
    pass


class UnsupportedAction(Exception):
    pass


class IDracManager:
    """
    Main Class, that interact with iDRAC via REST API interface.
    """
    _registry = {t: {} for t in ApiRequestType}

    def __init__(self, idrac_ip: Optional[str] = "",
                 idrac_username: Optional[str] = "root",
                 idrac_password: Optional[str] = "",
                 insecure: Optional[bool] = False,
                 x_auth: Optional[str] = None):
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
        self.content_type = {'Content-Type': 'application/json; charset=utf-8'}
        self.json_content_type = {'Content-Type': 'application/json; charset=utf-8'}

        # run time
        self.action_targets = None
        self.api_endpoints = None

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
    def invoke(cls, api_call: ApiRequestType, name: str, **kwargs) -> CommandResult:
        """Main interface uses to invoke a command.
        :param api_call:
        :param name:
        :param kwargs:
        :return:
        """
        z = cls._registry[api_call]
        disp = z[name]
        _idrac_ip = kwargs.pop("idrac_ip")
        _username = kwargs.pop("username")
        _password = kwargs.pop("password")

        inst = disp(idrac_ip=_idrac_ip,
                    idrac_username=_username,
                    idrac_password=_password)
        return inst.execute(**kwargs)

    async def async_invoke(cls, api_call: ApiRequestType, name: str, **kwargs) -> CommandResult:
        """Main interface uses to invoke a command.
        :param api_call:
        :param name:
        :param kwargs:
        :return:
        """
        z = cls._registry[api_call]
        disp = z[name]
        _idrac_ip = kwargs.pop("idrac_ip")
        _username = kwargs.pop("username")
        _password = kwargs.pop("password")

        inst = disp(idrac_ip=_idrac_ip,
                    idrac_username=_username,
                    idrac_password=_password)
        return inst.execute(**kwargs)

    async def api_async_get_call(self, loop, r, hdr: Dict):
        """Make api request either with x-auth authentication header or base.
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
            return loop.run_in_executor(None,
                                        functools.partial(requests.get, r,
                                                          verify=self._is_verify_cert,
                                                          headers=headers))
        else:
            return loop.run_in_executor(None,
                                        functools.partial(requests.get, r,
                                                          verify=self._is_verify_cert,
                                                          auth=(self._username, self._password)))

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

    def api_get_call(self, r, hdr: Dict):
        """Make api request either with x-auth authentication header or base.
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
            return requests.get(r, verify=self._is_verify_cert, headers=headers)
        else:
            return requests.get(r, verify=self._is_verify_cert,
                                auth=(self._username, self._password))

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
                                   headers=headers)
        else:
            return requests.delete(r, verify=self._is_verify_cert,
                                   auth=(self._username, self._password),
                                   headers=headers)

    def sync_invoke(self, api_call: ApiRequestType, name: str, **kwargs):
        """Synchronous invocation of target command
        :param api_call: A enum for command.
        :param name: A name for command to differentiate sub-commands.
        :param kwargs: Args passed to a command.
        :return: Return result depends on actual command.
        """
        kwargs.update({"idrac_ip": self._idrac_ip,
                       "username": self._username,
                       "password": self._password})
        return self.invoke(api_call, name, **kwargs)

    def fetch_job(self, job_id: str,
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
                            percent_done = int(resp_data['PercentComplete'])
                            if percent_done > last_update:
                                last_update = percent_done
                                inc = percent_done - pbar.n
                                pbar.update(n=inc)
                            time.sleep(sleep_time)
                else:
                    print(resp.status_code)
                    time.sleep(sleep_time)
                    print("Unknown status code")

    @staticmethod
    async def async_default_error_handler(response):
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code == 401:
            raise AuthenticationFailed("Authentication failed.")
        if response.status_code != 200:
            raise UnexpectedResponse(f"Failed acquire result. Status code {response.status_code}")

    @staticmethod
    def default_error_handler(response):
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code == 401:
            raise AuthenticationFailed("Authentication failed.")
        if response.status_code == 404:
            error_msg = IDracManager.parse_error(IDracManager, response)
            raise ResourceNotFound(error_msg)
        if response.status_code != 200:
            raise UnexpectedResponse(f"Failed acquire result. Status code {response.status_code}")

    def check_api_version(self):
        """Check Dell LLC server API set
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
    def default_json_printer(cls, json_data,
                             sort: Optional[bool] = True,
                             indents: Optional[int] = 4):
        """json default stdout printer.
        :param cls:
        :param json_data:
        :param indents:
        :param sort:
        :return:
        """
        if isinstance(json_data, str):
            json_raw = json.dumps(json.loads(json_data), sort_keys=sort, indent=indents)
        else:
            json_raw = json.dumps(json_data, sort_keys=sort, indent=indents)

        print(json_raw)

    @staticmethod
    def _get_actions(cls, json_data):

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
    def discover_redfish_actions(cls, json_data):
        """Discover all redfish action, args and args choices.
        :param json_data:
        :return:
        """
        action_dict = {}

        unfiltered_actions, full_redfish_names = cls._get_actions(cls, json_data)
        for ra in unfiltered_actions.keys():
            if 'target' not in unfiltered_actions[ra]:
                continue
            action_tuple = unfiltered_actions[ra]
            if isinstance(action_tuple, Dict):
                arg_keys = action_tuple.keys()
                action_dict[ra] = RedfishAction(action_name=ra,
                                                target=action_tuple['target'],
                                                full_redfish_name=full_redfish_names[ra])
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

    def api_post_call(self, req: str, payload: str, hdr: dict):
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
            return requests.post(req,
                                 data=payload,
                                 verify=self._is_verify_cert,
                                 headers=headers)
        else:
            return requests.post(req,
                                 data=payload,
                                 verify=self._is_verify_cert,
                                 headers=headers,
                                 auth=(self._username, self._password))

    async def api_async_post_call(self, loop, req: str, payload: str, hdr: Dict):
        """Make post api request either with x-auth authentication header or base.
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
            return loop.run_in_executor(None,
                                        functools.partial(requests.post,
                                                          req,
                                                          data=payload,
                                                          verify=self._is_verify_cert,
                                                          headers=headers))
        else:
            return loop.run_in_executor(None,
                                        functools.partial(requests.post,
                                                          req,
                                                          data=payload,
                                                          headers=headers,
                                                          verify=self._is_verify_cert,
                                                          auth=(self._username, self._password)))

    async def api_async_post_until_complete(self, r: str, payload: str, hdr: Dict, loop=None):
        """Make async post api request until completion , it issues post with x-auth
        authentication header or base.
        :param payload:
        :param r:
        :param hdr:
        :param loop:
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_post_call(loop, r, payload, hdr)
        await self.async_default_post_success(await response)
        return await response

    def api_patch_call(self, req: str, payload: str, hdr: dict):
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
        """Make post api request either with x-auth authentication header or base.
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
            return loop.run_in_executor(None,
                                        functools.partial(requests.patch,
                                                          req,
                                                          data=payload,
                                                          verify=self._is_verify_cert,
                                                          headers=headers))
        else:
            return loop.run_in_executor(None,
                                        functools.partial(requests.patch,
                                                          req,
                                                          data=payload,
                                                          verify=self._is_verify_cert,
                                                          headers=headers,
                                                          auth=(self._username, self._password)))

    @staticmethod
    def parse_error(cls, error_response):
        """Parse error msg from JSON error response
        :param cls:
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
    def default_patch_success(cls, response) -> bool:
        """Default patch success handler
        Default handler to check patch request respond.

        :param cls:
        :param response:
        :return: True if patch msg succeed
        :raise PatchFailed if patch failed
        """
        if response.status_code == 200 or response.status_code == 202:
            return True
        else:
            err_msg = IDracManager.parse_error(IDracManager, response)
            raise PatchFailed(f"{err_msg}\nHTTP Status code: {response.status_code}")

    @staticmethod
    def default_post_success(cls, response, expected=204) -> bool:
        """Default post success handler

        Default handler to check post request respond.

        :param expected:
        :param cls:
        :param response:
        :return: True if patch msg succeed
        :raise PatchFailed if patch failed
        """
        if response.status_code == expected:
            return True
        if response.status_code == 200 or response.status_code == 202 or response.status_code == 204:
            return True
        else:
            err_msg = IDracManager.parse_error(IDracManager, response)
            raise PostFailed(f"{err_msg}\nHTTP Status code: {response.status_code}")

    @staticmethod
    async def async_default_post_success(response):
        """Default error handler.
        :param response:
        :return:
        """
        return IDracManager.default_post_success(IDracManager, response)

    @staticmethod
    async def async_default_patch_success(response):
        """Default error handler.
        :param response:
        :return:
        """
        return IDracManager.default_patch_success(IDracManager, response)
