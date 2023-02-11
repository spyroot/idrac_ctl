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

https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v4.x-series/idrac9_4.00.00.00_redfishapiguide_pub/redfish-resources?guid=guid-d3e85da8-5d22-4eb1-82ff-d2fdd4cd7730&lang=en-us

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
from datetime import datetime
from functools import cached_property

from idrac_ctl.custom_argparser.customer_argdefault import CustomArgumentDefaultsHelpFormatter
from idrac_ctl.shared import ApiRequestType, RedfishAction, ScheduleJobType, IDRAC_JSON, IDRAC_API, JobApplyTypes
from .cmd_utils import save_if_needed
from .cmd_exceptions import AuthenticationFailed
from .cmd_exceptions import MissingMandatoryArguments
from .cmd_exceptions import PostRequestFailed
from .cmd_exceptions import MissingResource
from .cmd_exceptions import UnexpectedResponse
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import PatchRequestFailed
from .cmd_exceptions import DeleteRequestFailed
from .cmd_exceptions import UnsupportedAction
from .cmd_exceptions import InvalidArgumentFormat
from .cmd_exceptions import TaskIdUnavailable
from .shared import JobState

"""Each command encapsulate result in named tuple"""
CommandResult = collections.namedtuple("cmd_result",
                                       ("data", "discovered", "extra", "error"))

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
        self._default_method = "https://"
        self.logger = logging.getLogger(__name__)

        self.content_type = {'Content-Type': 'application/json; charset=utf-8'}
        self.json_content_type = {'Content-Type': 'application/json; charset=utf-8'}

        self._manage_servers_obs = []
        self._manage_chassis_obs = []
        # mainly to track query sent , for unit test
        self.query_counter = 0

        # run time
        self.action_targets = None
        self.api_endpoints = None
        self._post_success_responses = [200, 201, 202, 203, 204]
        self._patch_success_responses = [200, 201, 202, 203, 204]
        self._delete_success_responses = [200, 201, 202, 203, 204]

    @property
    def idrac_ip(self) -> str:
        return self._idrac_ip

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def x_auth(self) -> str:
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
                None, functools.partial(
                    requests.get, r,
                    verify=self._is_verify_cert,
                    headers=headers
                )
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
        :param name: a name for command to differentiate sub-commands
        :param api_call: enum i.e. a type command that we need invoke
        :param kwargs: arguments passed to a command
        :return: Return result depends on actual command,
                 encapsulated in generic CommandResult
        """
        if len(self._username) == 0:
            raise ValueError("Username is empty string.")
        if len(self._password) == 0:
            raise ValueError("Password is empty string.")
        if len(self._idrac_ip) == 0:
            raise ValueError("IDRAC IP is empty string.")

        kwargs.update(
            {
                "idrac_ip": self._idrac_ip,
                "username": self._username,
                "password": self._password
            }
        )
        return self.invoke(api_call, name, **kwargs)

    def get_job(self,
                job_id: str,
                data_type: Optional[str] = "json",
                do_async: Optional[bool] = False) -> dict:
        """Query information for particular job.
        :param job_id: iDRAC job_id JID_744718373591
        :param do_async: note async will subscribe to an event loop.
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"{self.idrac_members}/Oem/Dell/Jobs/{job_id}"
        return self.base_query(r, do_expanded=True, do_async=do_async).data

    def fetch_job(self,
                  job_id: str,
                  sleep_time: Optional[int] = 2,
                  wait_for: Optional[int] = 200,
                  wait_status: Optional[bool] = True,
                  wait_completion: Optional[bool] = True):
        """Synchronous fetch a job from iDRAC and wait for completion.
        :param wait_for:  by default, we wait status code 200 based on spec.
        :param job_id: job id as it returned from a task by idrac
        :param sleep_time: sleep and wait.
        :param wait_status: wait for http status.
        :param wait_completion: wait for completion a task.
        :return: Nothing
        :raise AuthenticationFailed MissingResource
        """
        last_update = 0
        percent_done = 0

        # job might be already done.
        jb = self.get_job(job_id)
        if IDRAC_JSON.JobState in jb:
            current_state = jb[IDRAC_JSON.JobState]
            if current_state == JobState.Completed.value:
                return self.api_success_msg(True, message=f"Job {job_id} completed.")
            if current_state == JobState.Failed.value:
                return self.api_success_msg(True, message=f"Job {job_id} failed.")

        with tqdm(total=100) as pbar:
            while True:
                resp = self.api_get_call(f"{self._default_method}{self.idrac_ip}"
                                         f"{IDRAC_API.IDRAC_TASKS}{job_id}", hdr={})
                if resp.status_code == 401:
                    AuthenticationFailed("Authentication failed.")
                elif resp.status_code == 404:
                    raise MissingResource(f"Task {job_id} not found.")

                elif resp.status_code == wait_for and wait_status:
                    resp_data = resp.json()
                    return resp_data
                elif resp.status_code == 202:
                    resp_data = resp.json()
                    if IDRAC_JSON.TaskStatus in resp_data and resp_data[IDRAC_JSON.TaskStatus] == 'OK':
                        if IDRAC_JSON.JobState in resp_data:
                            current_state = resp_data[IDRAC_JSON.JobState]
                        if IDRAC_JSON.PercentComplete in resp_data:
                            try:
                                percent_done = int(resp_data[IDRAC_JSON.PercentComplete])
                            except TypeError:
                                pass
                            if percent_done > last_update:
                                last_update = percent_done
                                inc = percent_done - pbar.n
                                pbar.update(n=inc)
                            time.sleep(sleep_time)
                elif wait_completion and current_state == JobState.Completed.value:
                    return resp_data
                elif wait_completion and current_state == JobState.Failed.value:
                    return resp_data
                else:
                    if IDRAC_JSON.JobState in resp_data:
                        current_state = resp_data[IDRAC_JSON.JobState]
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
            error_msg, json_error = IDracManager.parse_error(response)
            raise ResourceNotFound(error_msg)
        if response.status_code != 200:
            raise UnexpectedResponse(f"Failed acquire result. Status code {response.status_code}")

    def check_api_version(self):
        """Check Dell LLC Service API set
        :return:
        """
        headers = {}
        headers.update(self.json_content_type)
        r = f"{self._default_method}{self._idrac_ip}{IDRAC_API.IDRAC_DELL_MANAGERS}" \
            f"{IDRAC_API.IDRAC_LLC}"

        response = self.api_get_call(r, headers)
        self.default_error_handler(response)

        data = response.json()
        self.api_endpoints = data
        if IDRAC_JSON.Actions in self.api_endpoints:
            actions = self.api_endpoints[IDRAC_JSON.Actions]
            action_keys = actions.keys()
            self.action_targets = [actions[k]['target'] for k in action_keys]

        return self.api_endpoints, self.action_targets

    @staticmethod
    @abstractmethod
    def default_json_printer(json_data,
                             sort: Optional[bool] = True,
                             indents: Optional[int] = 4):
        """default json stdout printer, it mainly used for debug.
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

        if IDRAC_JSON.Actions not in json_data:
            return unfiltered_actions, full_redfish_names

        redfish_actions = json_data[IDRAC_JSON.Actions]
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
        if IDRAC_JSON.Members not in json_data:
            if IDRAC_JSON.Actions in json_data:
                return cls.discover_redfish_actions(cls, json_data)
            else:
                return action_dict

        member_data = json_data[IDRAC_JSON.Members]
        for m in member_data:
            if isinstance(m, dict):
                if IDRAC_JSON.Actions in m.keys():
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

    @cached_property
    def version_api(self, data_type: Optional[str] = "json") -> bool:
        """Return true if IDRAC version 6.0 i.e. a new version.
        :return:
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)
        r = f"{self._default_method}{self.idrac_ip}/redfish/v1/Managers" \
            f"/iDRAC.Embedded.1?$select=FirmwareVersion"
        response = self.api_get_call(r, headers)
        self.default_error_handler(response)
        data = response.json()
        if 'FirmwareVersion' in data:
            fw = data["FirmwareVersion"]
            self.logger.info(f"IDRAC firmware {fw}")
            return int(data["FirmwareVersion"].replace(".", "")) >= 6000000

        return False

    @staticmethod
    def filter_attribute(cls,
                         json_data,
                         attr_filter: Optional[str]):
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
            ignore_error_code: Optional[int] = 0,
            loop=None) -> Tuple[requests.models.Response, bool]:
        """Make async post api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param r: request.
        :param hdr: http header
        :param ignore_error_code: error code that we need ignore.
        :param loop: asyncio loop
        :param payload: json payload
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_post_call(loop, r, payload, hdr)
        ok = await self.async_default_post_success(
            await response, ignore_error_code=ignore_error_code
        )
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
    def parse_error(error_response: requests.models.Response) -> Tuple[str, str]:
        """Default Parser for error msg from
        JSON error response based on iDRAC.
        :param error_response:
        :return:
        """
        err_msg = "Default error."
        messages = [""]
        err_resp = error_response.json()
        if 'error' in err_resp:
            err_data = err_resp['error']
            if 'message' in err_data:
                err_msg = err_resp['error']['message']
            if '@Message.ExtendedInfo' in err_data:
                messages = [m['Message'] for m in err_data['@Message.ExtendedInfo'] if 'Message' in m]
                extended_err = err_data['@Message.ExtendedInfo'][-1]
                err_msg = [f"{k}: {v}" for k, v in extended_err.items() if "@" not in k]
                err_msg = "\n".join(err_msg)

        return err_msg, " ".join(messages)

    @staticmethod
    def default_patch_success(cls,
                              response: requests.models.Response,
                              expected: Optional[int] = 200,
                              ignore_error_code: Optional[int] = 0) -> bool:
        """Default HTTP patch success handler
        Default handler to check patch request respond.

        :param cls:
        :param response: HTTP response
        :param expected:  Option status code that we caller consider success.
        :param ignore_error_code: error code to ignore.
        :return: True if patch msg succeed
        :raise PatchFailed if patch failed
        """
        if response.status_code == expected:
            return True

        if ignore_error_code > 0 and ignore_error_code == response.status_code:
            return False

        if response.status_code == 200 \
                or response.status_code == 202 or response.status_code == 204:
            return True
        else:
            err_msg, json_error = IDracManager.parse_error(response)
            e = PatchRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}", json_error=json_error
            )
            e.error_msg = json_error

    @staticmethod
    def default_post_success(cls,
                             response: requests.models.Response,
                             expected: Optional[int] = 204,
                             ignore_error_code: Optional[int] = 0) -> bool:
        """Default post success handler,  Check for status code.
        and raise exception.  Default handler to check post
        request respond.

        :param cls:
        :param response: HTTP response
        :param ignore_error_code: error code to ignore.
        :param expected:  Option status code that we caller consider success.
        :return: True if patch msg succeed
        :raise PostRequestFailed if POST Method failed
        """
        if response.status_code == expected:
            return True

        if ignore_error_code > 0 and ignore_error_code == response.status_code:
            return False

        if response.status_code == 200 \
                or response.status_code == 202 \
                or response.status_code == 204:
            return True
        else:
            err_msg, json_error = IDracManager.parse_error(response)
            raise PostRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}", json_error=json_error
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
            err_msg, json_error = IDracManager.parse_error(response)
            raise DeleteRequestFailed(
                f"{err_msg}\nHTTP Status code: "
                f"{response.status_code}", json_error=json_error
            )

    def api_async_del_until_complete(self, r, headers):
        pass

    @staticmethod
    async def async_default_post_success(response: requests.models.Response,
                                         ignore_error_code: Optional[int] = 0) -> bool:
        """Default error handler, for post
        :param response: response HTTP response.
        :param ignore_error_code: ignore HTTP statue error.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return IDracManager.default_post_success(
            IDracManager, response, ignore_error_code=ignore_error_code
        )

    @staticmethod
    async def async_default_delete_success(response: requests.models.Response) -> bool:
        """Default error handler, for post
        :param response: response HTTP response.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return IDracManager.default_delete_success(response)

    @staticmethod
    async def async_default_patch_success(response: requests.models.Response,
                                          ignore_error_code: Optional[int] = 0) -> bool:
        """Default error handler for patch http method.
        :param response: response HTTP response.
        :param ignore_error_code: ignore HTTP statue error.
        :return: True or False and if failed raise exception
        """
        return IDracManager.default_patch_success(
            IDracManager, response, ignore_error_code=ignore_error_code
        )

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
            r = f"{self._default_method}{self.idrac_ip}{resource}{self.expanded()}"
        else:
            r = f"{self._default_method}{self.idrac_ip}{resource}"

        if not do_async:
            response = self.api_get_call(r, headers)
            self.query_counter += 1
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
        return CommandResult(data, None, None, None)

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

        self.logger.debug(f"Issuing patch request to "
                          f"resource: {resource}, "
                          f"payload: {json.dumps(pd)}")

        ok = False
        err = None
        response = None
        try:
            r = f"{self._default_method}{self.idrac_ip}{resource}"
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
            err = pf

        return CommandResult(self.api_success_msg(ok), None, response, err)

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
        err = None
        response = None
        try:
            r = f"{self._default_method}{self.idrac_ip}{resource}"
            if not do_async:
                response = self.api_post_call(r, json.dumps(pd), headers)
                if verbose:
                    self.logger.debug(f"received status code {response.status_code}")
                    self.logger.debug(f"received status code {response.headers}")
                    self.logger.debug(f"received {response.raw}")
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
            err = pf
            self.logger.critical(pf, exc_info=self._is_debug)

        return CommandResult(self.api_success_msg(ok), None, response, err)

    @staticmethod
    def api_success_msg(status: bool,
                        message_key: Optional[str] = "message",
                        message=None) -> Dict:
        """A default api success respond.
        :param status: a status true of false
        :param message_key: key we need add extra
        :param message: message information data
        :return: a dict
        """
        if message is not None:
            return {
                "Status": status,
                message_key: message
            }

        return {"Status": status}

    @staticmethod
    def api_is_change_msg(status: bool,
                          message_key: Optional[str] = "message",
                          message=None) -> Dict:
        """A default api msg when no change applied.
        :param status: a status true of false
        :param message_key: key we need add extra
        :param message: message information data
        :return: a dict
        """
        if message is not None:
            return {
                "Changed": status,
                message_key: message
            }
        return {"Changed": status}

    def reboot(self,
               do_watch: Optional[bool] = False,
               power_state_attr: Optional[str] = "PowerState",
               default_reboot_type: Optional[str] = "ForceRestart") -> dict:
        """Check if power state is on, reboots a host.
        :return: return a dict stora if operation succeed..
        """
        result_data = {}

        # state of chassis
        cmd_chassis = self.sync_invoke(
            ApiRequestType.ChassisQuery,
            "chassis_service_query",
            data_filter=power_state_attr
        )

        if isinstance(cmd_chassis.data, dict) and 'PowerState' in cmd_chassis.data:
            pd_state = cmd_chassis.data[power_state_attr]
            if pd_state == 'On':
                cmd_reboot = self.sync_invoke(
                    ApiRequestType.RebootHost, "reboot",
                    reset_type=default_reboot_type,
                    do_watch=do_watch
                )
                if 'Status' in cmd_reboot.data:
                    result_data.update(
                        {
                            "Reboot": cmd_reboot.data['Status']
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

    @cached_property
    def idrac_firmware(self) -> str:
        """Shared method return idrac firmware
        :return: str: firmware.
        """
        api_return = self.base_query(self.idrac_members,
                                     key=IDRAC_JSON.FirmwareVersion)
        return api_return.data

    def idrac_last_reset(self) -> datetime:
        """Shared method return idrac last reset time"""
        idrac_reset_time = None
        api_return = self.base_query(self.idrac_members,
                                     key=IDRAC_JSON.LastResetTime)
        try:
            idrac_reset_time = datetime.fromisoformat(api_return.data)
        except ValueError as ve:
            self.logger.error(ve)
        return idrac_reset_time

    def idrac_current_time(self) -> datetime:
        """Shared method return idrac current time, if idrac return none ISO format
        :return: datetime
        """
        idrac_time = None
        api_return = self.base_query(self.idrac_members,
                                     key=IDRAC_JSON.Datatime)
        try:
            idrac_time = datetime.fromisoformat(api_return.data)
        except ValueError as ve:
            self.logger.error(ve)
        return idrac_time

    @staticmethod
    def local_time_iso():
        """local time in iso format"""
        current_date = datetime.now()
        return current_date.isoformat()

    def idrac_time_offset(self):
        """Shared method return idrac current time"""
        api_resp = self.base_query(self.idrac_members,
                                   key=IDRAC_JSON.DateTimeLocalOffset)
        return api_resp.data

    @cached_property
    def idrac_manage_chassis(self) -> str:
        """Shared method return idrac managed chassis list as json
        :return: str: manage chassis i.e. /redfish/v1/Chassis/System.Embedded.1
        """
        api_resp = self.base_query(self.idrac_members, key=IDRAC_JSON.Links)
        if api_resp.data is not None and IDRAC_JSON.ManageChassis in api_resp.data:
            if isinstance(api_resp.data, dict):
                manage_chassis = api_resp.data[IDRAC_JSON.ManageChassis]
                self._manage_chassis_obs = manage_chassis
                return self.value_from_json_list(
                    manage_chassis, IDRAC_JSON.Data_id
                )
        else:
            self.logger.error("")
        return ""

    @cached_property
    def idrac_members(self) -> str:
        """Shared method return idrac manage members servers list as json
        /redfish/v1/Managers/iDRAC.Embedded.1
        """
        cmd_result = self.base_query(f"{IDRAC_API.IDRAC_MANAGER}", key=IDRAC_JSON.Members)
        return self.value_from_json_list(cmd_result.data, IDRAC_JSON.Data_id)

    @staticmethod
    def value_from_json_list(json_obj, k):
        """Parse json object dict.  If resp is json list [] get a key from last element
        otherwise if a dict return value from a dict.
        """
        if isinstance(json_obj, list) and len(json_obj) > 0:
            list_flat = json_obj[-1]
            if isinstance(list_flat, dict):
                if k in list_flat:
                    return list_flat[k]
        elif isinstance(json_obj, dict):
            if k in json_obj:
                return json_obj[k]
        elif isinstance(json_obj, str):
            return json_obj

    @cached_property
    def idrac_manage_servers(self) -> str:
        """Shared method return idrac managed servers list as json
        "/redfish/v1/Systems/System.Embedded.1"
        """
        api_resp = self.base_query(self.idrac_members, key=IDRAC_JSON.Links)
        if api_resp.data is not None and IDRAC_JSON.ManagerServers in api_resp.data:
            if isinstance(api_resp.data, dict):
                manage_servers = api_resp.data[IDRAC_JSON.ManagerServers]
                self._manage_servers_obs = manage_servers
                return self.value_from_json_list(
                    manage_servers, IDRAC_JSON.Data_id
                )
        else:
            self.logger.error("")
        return ""

    @cached_property
    def idrac_id(self):
        """Shared method return idrac id, System.Embedded.1"""
        self.base_query(self.idrac_manage_servers, key=IDRAC_JSON.Id)
        api_resp = self.base_query(self.idrac_manage_servers, key=IDRAC_JSON.Id)
        if api_resp is None:
            self.logger.critical(f"failed obtain {IDRAC_JSON.Id}")
        return api_resp.data

    @staticmethod
    def base_parser(is_async: Optional[bool] = True,
                    is_file_save: Optional[bool] = True,
                    is_expanded: Optional[bool] = True,
                    is_remote_share: Optional[bool] = False,
                    is_reboot: Optional[bool] = False):
        """This idrac_ctl optional parser for all sub command.
        Each sub-command can add additional optional flags and args.
        :return: argparse.ArgumentParser
        """
        cmd_parser = argparse.ArgumentParser(
            add_help=False, formatter_class=CustomArgumentDefaultsHelpFormatter
        )

        output_parser = cmd_parser.add_argument_group('output', 'Output related options')
        chassis_parser = cmd_parser.add_argument_group('chassis', 'Chassis state options')

        if is_async:
            cmd_parser.add_argument(
                '-a', '--async', action='store_true',
                required=False, dest="do_async",
                default=False,
                help="will use async call."
            )

        if is_expanded:
            output_parser.add_argument(
                '-e', '--expanded', action='store_true',
                required=False, dest="do_expanded",
                default=False,
                help="expanded view, depend. it allows viewing more detail IDRAC data."
            )
        if is_file_save:
            output_parser.add_argument(
                '-f', '--filename', required=False, default="",
                type=str,
                help="filename, if we need to save a respond to a file."
            )

        if is_reboot:
            chassis_parser.add_argument(
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
        if IDRAC_JSON.Location not in resp_hdr:
            raise TaskIdUnavailable(
                "There is no location in the response header. "
                "(not all api create job id)"
            )
        location = response.headers[IDRAC_JSON.Location]
        job_id = location.split("/")[-1]
        return job_id

    @staticmethod
    def schedule_job_request(
            reboot_type: ScheduleJobType,
            start_time_isofmt: Optional[str],
            duration_time: Optional[int]) -> dict:
        """Create a JSON payload for schedule a job.

        :param reboot_type: reboot type, ScheduleJobType
        :param start_time_isofmt: start time for a job in ISO format.
        :param duration_time: duration for a job
        :return:
        """
        if reboot_type == ScheduleJobType.NoReboot:
            pd = {
                IDRAC_JSON.RedfishSettingsApplyTime: {
                    IDRAC_JSON.ApplyTime: JobApplyTypes.InMaintenance,
                    IDRAC_JSON.MaintenanceWindowStartTime: start_time_isofmt,
                    IDRAC_JSON.MaintenanceWindowDuration: duration_time
                }
            }
        elif reboot_type == ScheduleJobType.AutoReboot:
            pd = {
                IDRAC_JSON.RedfishSettingsApplyTime: {
                    IDRAC_JSON.ApplyTime: JobApplyTypes.AtMaintenance,
                    IDRAC_JSON.MaintenanceWindowStartTime: start_time_isofmt,
                    IDRAC_JSON.MaintenanceWindowDuration: duration_time
                }
            }
        elif reboot_type == ScheduleJobType.OnReset:
            pd = {
                IDRAC_JSON.RedfishSettingsApplyTime: {
                    IDRAC_JSON.ApplyTime: JobApplyTypes.OnReset
                }
            }
        elif reboot_type == ScheduleJobType.Immediate:
            pd = {
                IDRAC_JSON.RedfishSettingsApplyTime: {
                    IDRAC_JSON.ApplyTime: JobApplyTypes.Immediate
                }
            }
        else:
            raise InvalidArgumentFormat(
                "Invalid settings apply time.")
        return pd

    def parse_task_id(self, data):
        """Parses input data and try to get a job id from the header
        or http response.
        :param data:  http response or CommandResult
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
            logging.debug(f"idrac api returned {job_id} in the header.")
            return job_id
        except TaskIdUnavailable as tiu:
            pass
        except UnexpectedResponse as ur:
            logging.debug(ur, exc_info=self._is_debug)

        try:
            # try to get from the response , it an optional check.
            if job_id is None:
                job_id = self.job_id_from_respond(resp)
                logging.debug(f"idrac api returned {job_id} in the header.")
        except TaskIdUnavailable as tiu:
            pass
        except UnexpectedResponse as _:
            pass

        if job_id is not None:
            data = self.fetch_job(job_id)
            return data

        return {}

    @staticmethod
    def make_future_job_ts(start_date: str,
                           start_time: str,
                           is_json_string=False) -> str:
        """Make a future time for a maintenance task.
        It takes start_date in format YYYY-MM-DD
        and starts time in format HH:MM:SS and return
        JSON string time in ISO format.

        "2023-02-08T01:01:01.000001"

       :param start_date: start date for a job YYYY-MM-DD
       :param start_time: a start time for a job HH:MM:SS
       :param is_json_string return python string or JSON string.
       :raise: MissingMandatoryArguments if mandatory args missing.
       :raise: InvalidArgumentFormat if format of the input is invalid.
       """
        if start_date is None or len(start_date) == 0:
            raise MissingMandatoryArguments(
                "A maintenance job requires a start date.")

        if start_time is None or len(start_time) == 0:
            raise MissingMandatoryArguments(
                "A maintenance job requires a start time.")
        try:
            local_timestamp = datetime.now()
            ts = f'{start_date}T{start_time}.000001'
            start_timestamp = datetime.fromisoformat(ts)
            if start_timestamp < local_timestamp:
                raise InvalidArgumentFormat(
                    f"Start time is in the past local time "
                    f"{str(local_timestamp)} {str(start_timestamp)}")

            # note we always parse to make sure we can convert.
            json_str = json.dumps(start_timestamp.isoformat())
            if is_json_string:
                return json_str
            else:
                return start_timestamp.isoformat()
        except ValueError as ve:
            raise InvalidArgumentFormat(str(ve))
        except TypeError as te:
            raise InvalidArgumentFormat(str(te))

    def create_apply_time_req(self,
                              apply: str,
                              start_date: str,
                              start_time: str,
                              default_duration):
        """
        :param start_date
        :param start_time
        :param default_duration
        :param apply time auto-boot, maintenance, on-reset
        :raise InvalidArgumentFormat
        """
        if apply.strip().lower() == "auto-boot":
            start_timestamp = self.make_future_job_ts(start_date, start_time)
            return self.schedule_job_request(
                ScheduleJobType.AutoReboot,
                start_time_isofmt=start_timestamp,
                duration_time=default_duration
            )
        elif apply.strip().lower() == "maintenance":
            start_timestamp = self.make_future_job_ts(start_date, start_time)
            return self.schedule_job_request(
                ScheduleJobType.NoReboot,
                start_time_isofmt=start_timestamp,
                duration_time=default_duration
            )
        elif apply.strip().lower() == "on-reset":
            return self.schedule_job_request(
                ScheduleJobType.OnReset,
                start_time_isofmt=None,
                duration_time=None
            )
        else:
            ValueError("Unknown apply time")

        return {}
