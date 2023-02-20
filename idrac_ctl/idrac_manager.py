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
import functools
import json
import logging
import time
from abc import abstractmethod
from datetime import datetime
from functools import cached_property
from typing import Optional, Tuple, Dict

import requests
from tqdm import tqdm

from .redfish_exceptions import RedfishException
from .redfish_exceptions import RedfishUnauthorized
from .redfish_exceptions import RedfishForbidden

from .redfish_manager import RedfishManager
from .redfish_task_state import TaskState
from .redfish_task_state import TaskStatus
from .redfish_shared import RedfishJsonSpec, RedfishJson

from idrac_ctl.custom_argparser.customer_argdefault import CustomArgumentDefaultsHelpFormatter
from idrac_ctl.redfish_manager import CommandResult
from idrac_ctl.idrac_shared import ApiRequestType, HTTPMethod, CliJobTypes, IDRACJobType, PowerState
from idrac_ctl.idrac_shared import ApiRespondString
from idrac_ctl.idrac_shared import IDRAC_API
from idrac_ctl.idrac_shared import IDRAC_JSON
from idrac_ctl.idrac_shared import IdracApiRespond
from idrac_ctl.idrac_shared import JobApplyTypes
from idrac_ctl.idrac_shared import RedfishAction
from idrac_ctl.idrac_shared import ResetType as ResetType
from idrac_ctl.idrac_shared import ScheduleJobType
from .idrac_shared import JobState

from .cmd_exceptions import AuthenticationFailed
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import PostRequestFailed
from .cmd_exceptions import DeleteRequestFailed

from .cmd_exceptions import InvalidArgumentFormat
from .cmd_exceptions import MissingMandatoryArguments
from .cmd_exceptions import PatchRequestFailed
from .cmd_exceptions import UnexpectedResponse
from .cmd_exceptions import UnsupportedAction

module_logger = logging.getLogger('idrac_ctl.idrac_manager')


class IDracManager(RedfishManager):
    """
    IDracManager Class, interact with iDRAC via REST API interface
    """

    _registry = {t: {} for t in ApiRequestType}

    def __init__(self,
                 idrac_ip: Optional[str] = "",
                 idrac_username: Optional[str] = "root",
                 idrac_password: Optional[str] = "",
                 insecure: Optional[bool] = False,
                 x_auth: Optional[str] = None,
                 is_debug: Optional[bool] = False,
                 log_level=logging.NOTSET):
        """Default constructor for idrac requires credentials.
           By default, iDRAC Manager uses json to serialize a data to callee
           and uses json content type.

        :param idrac_ip: idrac mgmt IP address
        :param idrac_username: idrac username default is root
        :param idrac_password: idrac password.
        :param insecure: by default, we use insecure SSL
        :param x_auth: X-Authentication header.
        """
        super().__init__(redfish_ip=idrac_ip,
                         redfish_username=idrac_username,
                         redfish_password=idrac_username,
                         insecure=insecure,
                         x_auth=x_auth,
                         is_debug=is_debug)
        self._idrac_ip = idrac_ip
        self._username = idrac_username
        self._password = idrac_password
        self._is_verify_cert = insecure
        self._x_auth = x_auth
        self._is_debug = is_debug
        self._default_method = "https://"
        self.logger = logging.getLogger(__name__)
        self._logger_level = log_level
        self.logger.setLevel(self._logger_level)

        self.content_type = {'Content-Type': 'application/json; charset=utf-8'}
        self.json_content_type = {'Content-Type': 'application/json; charset=utf-8'}

        self._manage_servers_obs = []
        self._manage_chassis_obs = []
        # mainly to track query sent , for unit test
        self.query_counter = 0

        # mapping between rest API respond to respected
        # string that we report to apper layer.
        self._api_respond_to_string = {
            IdracApiRespond.Ok: ApiRespondString.Ok,
            IdracApiRespond.Error: ApiRespondString.Error,
            IdracApiRespond.Success: ApiRespondString.Success,
            IdracApiRespond.AcceptedTaskGenerated: ApiRespondString.AcceptedTaskGenerated,

        }

        # a mapping from http status code to result of request.
        # idrac not consistent with return code, so it not very clear
        # case when 200 is ok and 201 is something else. So it API per API
        # Thus default success has extra field, so we can always
        # pass what we expect for particular cmd.

        #  Redfish spec 202 Request has been accepted for processing
        #  but the processing has not been completed
        self._http_code_mapping = {
            200: IdracApiRespond.Ok,
            201: IdracApiRespond.Created,
            202: IdracApiRespond.AcceptedTaskGenerated,
            204: IdracApiRespond.Success,
        }

        # mapping a string state to enum, so each cmd can just check a state
        # without doing any string if else branches.
        self._job_state_mapping = {
            "Scheduled": JobState.Scheduled,
            "Running": JobState.Running,
            "Completed": JobState.Completed,
            "Downloaded": JobState.Downloaded,
            "Downloading": JobState.Downloading,
            "Scheduling": JobState.Scheduling,
            "Waiting": JobState.Waiting,
            "Failed": JobState.Failed,
            "CompletedWithErrors": JobState.CompletedWithErrors,
            "RebootFailed": JobState.RebootFailed,
            "RebootCompleted": JobState.RebootCompleted,
            "RebootPending": JobState.RebootPending,
            "PendingActivation": JobState.PendingActivation,
            "Unknown": JobState.Unknown,
        }

        # mapping a task state string to enum
        # without doing any string if else branches.
        self._task_state_mapping = {
            "New": TaskState.New,
            "Running": TaskState.Starting,
            "Starting": TaskState.Starting,
            "Suspended": TaskState.Suspended,
            "Interrupted": TaskState.Interrupted,
            "Pending": TaskState.Pending,
            "Stopping": TaskState.Stopping,
            "Completed": TaskState.Completed,
            "Killed": TaskState.Killed,
            "Exception": TaskState.Exception,
            "Service": TaskState.Service,
            "Canceling": TaskState.Canceling,
            "Cancelled": TaskState.Cancelled
        }

        # mapping from cli to job types
        self._cli_job_type_mapping = {
            CliJobTypes.Bios_Config.value: IDRACJobType.BIOSConfiguration.value,
            CliJobTypes.OsDeploy.value: IDRACJobType.OSDeploy.value,
            CliJobTypes.FirmwareUpdate.value: IDRACJobType.FirmwareUpdate.value,
            CliJobTypes.RebootNoForce.value: IDRACJobType.RebootNoForce.value
        }

        # mapping from string to task status enum
        self._task_status_mapping = {
            "ok": TaskStatus.Ok,
            "warning": TaskStatus.Warning,
            "critical": TaskStatus.Critical
        }

        self._redfish_error = None

        # run time
        self.action_targets = None
        self.api_endpoints = None

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

    async def async_invoke(
            cls, api_call: ApiRequestType, name: str, **kwargs) -> CommandResult:
        """Main interface uses to invoke a command.
        :param api_call: api request type is enum for each cmd.
        :param name: a name.
        :param kwargs: argument passed to command
        :return: CommandResult
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

    async def api_async_get_call(self, loop, req, hdr: Dict):
        """Make api asynced requests either with x-auth authentication
         header or base authentication.
        If event loop is none it will create one.
        :param loop: asyncio event loop
        :param req: request
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
                    requests.get, req,
                    verify=self._is_verify_cert,
                    headers=headers
                )
            )
        else:
            return loop.run_in_executor(
                None, functools.partial(
                    requests.get, req,
                    verify=self._is_verify_cert,
                    auth=(self._username, self._password)
                )
            )

    async def api_async_get_until_complete(
            self, req, hdr: Dict, loop=None) -> requests.models.Response:
        """Make asyncio request,
        :param req: request
        :param hdr: HTTP headers
        :param loop: a default loop, if loop is None method will create
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_get_call(loop, req, hdr)
        await self.async_default_error_handler(await response)
        return await response

    def api_get_call(
            self, req: str, hdr: Dict) -> requests.models.Response:
        """Make api request either with x-auth authentication header or idrac_ctl.
        :param req:  request
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
                req, verify=self._is_verify_cert, headers=headers
            )
        else:
            return requests.get(
                req, verify=self._is_verify_cert,
                auth=(self._username, self._password)
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
        """Query information for particular job from dell oem.
        Respond is information about a specific configuration Job scheduled
        by or being executed by a Redfish service's Job Service.
        :param job_id: iDRAC job_id JID_744718373591
        :param do_async: note async will subscribe to an event loop.
        :param data_type: json or xml
        :return: CommandResult.
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        r = f"{self.idrac_members}/Oem/Dell/Jobs/{job_id}"
        return self.base_query(r, do_expanded=True, do_async=do_async).data

    @staticmethod
    def update_progress(resp_data, old_value):
        """Get a percent computed from respond, if something dodgy
        will return old value.
        :param resp_data: response
        :param old_value:  old value
        :return:
        """
        # update percent_done and progress bar
        if IDRAC_JSON.PercentComplete in resp_data:
            try:
                percent_done = int(resp_data[IDRAC_JSON.PercentComplete])
                return percent_done
            except TypeError:
                pass

        return old_value

    def get_task_state(self, resp: requests.models.Response) -> Tuple[TaskState, TaskStatus]:
        """Parse response and return task state and status,
        if resp has no json payload and JSONDecodeError raised , return Unknown state.

        if Task Status or TaskState absent from response UnexpectedResponse raised.

        :param resp: a requests.models.Response object.
        :return:  idrac_ctl.TaskState and idrac_ctl.TaskStatus
        :raise  idrac_ctl.UnexpectedResponse: If the response body does not
            contain a task state.
        """
        try:
            resp_data = resp.json()
        except requests.exceptions.JSONDecodeError as json_err:
            self.logger.error(
                f"failed parse response to get a task state. {str(json_err)}"
            )
            return TaskState.Unknown, TaskStatus.Warning

        # dodge case
        if IDRAC_JSON.TaskStatus not in resp_data or IDRAC_JSON.TaskState not in resp_data:
            raise UnexpectedResponse(f"IDRAC returned a {resp_data}, neither task state nor status is present..")

        resp_state = resp_data[IDRAC_JSON.TaskState]
        resp_status = resp_data[IDRAC_JSON.TaskStatus]

        # update state and status.
        task_state = self._task_state_mapping[resp_state]
        task_status = self._task_status_mapping[resp_status.lower()]
        return task_state, task_status

    def fetch_task(self,
                   task_id: str,
                   sleep_time: Optional[int] = 10,
                   wait_for: Optional[int] = 0,
                   wait_for_state: Optional[TaskState] = TaskState.Unknown) -> TaskState:

        """Synchronous fetch a job from iDRAC and wait for job completion.

        A job in idrac is the Task and contains information about a task
        that the Redfish Task Service schedules or executes.

        Tasks represent operations that we want to wait.
        Example we applied a change that create a task, and we need wait for completion.

        Note: that caller can provide wait_for_state that will unblock waiting loop,
        for example if we don't want wait for completion or error.  i.e.
        Running or Scheduled is sufficient criterion.
        (It useful for async io type of request)

        if server return  404 or  410:
        - if a state was update caller will get last known state.
        - if a state never updated caller will get Unknown.

        THus, for a caller it amke sense to re-check task services.

        :param wait_for: by default, we wait status code 200 based on spec.
                         in case API return something else. 204 for example.
        :param task_id: task id as it returned from a task by task services.
        :param sleep_time: a default sleep and wait, if server ask for retry_after, it takes precedence
                           only if retry_after > sleep_time.
        :param wait_for_state: wait a specific state. Example caller only care
                               it Running and will resume later to monitor progress

        :return: Nothing
        :raise AuthenticationFailed MissingResource
        """
        last_update = 0
        percent_done = 0

        # job might be already done.
        jb = self.get_job(task_id)

        # if job scheduler or scheduling it make sense to wait otherwise we return state
        # we expect a JobState
        if IDRAC_JSON.JobState in jb:

            current_state = jb[IDRAC_JSON.JobState]
            if current_state not in self._job_state_mapping:
                raise UnexpectedResponse(f"IDRAC returned a {current_state} job type that we don't know.")
            _ = self._job_state_mapping[current_state]
            if current_state == JobState.Scheduled.value or current_state == JobState.Scheduling.value \
                    or current_state == JobState.Running.value:
                self.logger.info(f"Job {task_id} is {current_state}.. waiting for completion.")
            else:
                self.logger.info(f"Job {task_id} is {current_state}..bouncing off.")
                return self._job_state_mapping[current_state]

        # in case server will ask to wait.
        retry_after = 0
        # initial state we don't know
        task_state = TaskState.Unknown
        with tqdm(total=100) as pbar:
            while True:
                # /redfish/v1/TaskService/Tasks/{TaskId}
                resp = self.api_get_call(f"{self._default_method}{self.idrac_ip}"
                                         f"{IDRAC_API.Tasks}{task_id}", hdr={})

                if 'Retry-After' in resp.headers:
                    retry_after = int(resp.headers["Retry-After"])
                    self.logger.info(f"Remote server responded with Retry-After {retry_after}")
                print(f"fetch status code {resp.status_code}")
                if resp.status_code == 401:
                    self.logger.error(f"task service returned 401")
                    AuthenticationFailed("Authentication failed.")
                # if server failed, meanwhile HTTP exception propagate
                # up on the stack.
                if resp.status_code > 499:
                    self.logger.critical(f"task service return http error code {resp.status_code}")
                    break
                # Cancellation: A subsequent GET request on the task monitor URI
                # returns either the HTTP 410 Gone or 404 Not Found status code.
                elif resp.status_code == 404 or resp.status_code == 410:
                    self.logger.info(f"task service returned {resp.status_code}")
                    # at the end we check a state and return it might fail, exception etc.
                    break
                # if client expect something else than 200 or something else, we return result.
                elif 0 < wait_for == resp.status_code:
                    task_state, task_status = self.get_task_state(resp)
                    return task_state
                # As long as the operation is in process, the service shall return the HTTP 202 Accepted status code
                # when the client performs a GET request on the task monitor URI.
                elif resp.status_code == 202:
                    self.logger.info(f"task service returned 202")
                    # state acquisition and update state
                    resp_data = resp.json()
                    task_state, task_status = self.get_task_state(resp)
                    self.logger.info(f"Updating state, new state "
                                     f"{task_state.value}, status {task_status.value}")

                    # update description so caller see.
                    pbar.set_description(task_state.value)
                    if task_status == TaskStatus.Critical or task_status == TaskStatus.Warning:
                        # we bounce, if status not ok
                        break

                    percent_done = self.update_progress(resp_data, percent_done)
                    if percent_done > last_update:
                        last_update = percent_done
                        inc = percent_done - pbar.n
                        pbar.update(n=inc)

                    # update retry time, we've been asked
                    if retry_after > sleep_time:
                        sleep_time = retry_after
                    time.sleep(sleep_time)

                # The appropriate HTTP status code, such as but not limited to 200 OK
                # for most operations or 201 Created for POST to create a resource.
                # if client passed wait_for for example 204 we need have handle for 200
                elif resp.status_code == 200:
                    task_state, task_status = self.get_task_state(resp)
                    self.logger.info(
                        f"Server return status code 200, Task state {task_state.value}, {task_status.value}")
                    return task_state
                # client wait for specific state
                elif task_state == wait_for_state:
                    self.logger.info(f"caller asked for wait for a state {wait_for_state.value}")
                    task_state, task_status = self.get_task_state(resp)
                    return task_state
                else:
                    # in all other cases update state and go back sleep.
                    task_state, task_status = self.get_task_state(resp)
                    self.logger.error("unexpected status code", resp.status_code)
                    if retry_after > sleep_time:
                        sleep_time = retry_after
                    time.sleep(sleep_time)

        return task_state

    def default_error_handler(
            self, response: requests.models.Response) -> IdracApiRespond:
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code >= 200 or response.status_code < 300:
            if response.status_code in self._http_code_mapping:
                return self._http_code_mapping[response.status_code]

        if response.status_code == 401:
            raise AuthenticationFailed("Authentication failed.")
        elif response.status_code == 403:
            raise RedfishForbidden("access forbidden")
        elif response.status_code == 404:
            error_msg = RedfishManager.parse_error(response)
            raise ResourceNotFound(error_msg)
        if 401 <= response.status_code < 500:
            # we try to parse error.
            self._redfish_error = IDracManager.parse_error(response)
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
    def default_json_printer(
            json_data,
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

    def api_delete_call(
            self, req, hdr: Dict) -> requests.models.Response:
        """Make api request for delete method.
        :param req: request
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self.x_auth is not None:
            headers.update({'X-Auth-Token': self.x_auth})
            return requests.delete(
                req, verify=self._is_verify_cert,
                headers=headers
            )
        else:
            return requests.delete(
                req, verify=self._is_verify_cert,
                auth=(self._username, self._password),
                headers=headers
            )

    def api_post_call(
            self, req: str, payload: str, hdr: dict) -> requests.models.Response:
        """Make HTTP post request.
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

    async def api_async_post_call(
            self, loop, req: str, payload: str, hdr: Dict):
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
            hdr: Dict,
            loop=None,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0
    ) -> Tuple[requests.models.Response, IdracApiRespond]:
        """Make async patch api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param expected:
        :param ignore_error_code:
        :param r: request.
        :param hdr: http header.
        :param loop: asyncio loop
        :param payload: json payload
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_patch_call(loop, r, payload, hdr)
        api_respond_status = await self.async_default_patch_success(
            await response, expected=expected, ignore_error_code=ignore_error_code)
        return await response, api_respond_status

    async def api_async_delete_until_complete(
            self, r: str,
            payload: str,
            hdr: Dict,
            loop=None,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0
    ) -> Tuple[requests.models.Response, IdracApiRespond]:
        """Make async patch api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param expected:
        :param ignore_error_code:
        :param r: request.
        :param hdr: http header.
        :param loop: asyncio loop
        :param payload: json payload
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_delete_call(loop, r, payload, hdr)
        api_respond_status = await self.async_default_delete_success(
            await response, expected=expected, ignore_error_code=ignore_error_code)
        return await response, api_respond_status

    async def api_async_post_until_complete(
            self, r: str,
            payload: str,
            hdr: Dict,
            loop=None,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0
    ) -> Tuple[requests.models.Response, IdracApiRespond]:
        """Make async post api request until completion , it issues post with x-auth
        authentication header or idrac_ctl. Caller can use this in asyncio routine.

        :param expected:
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
        api_respond_status = await self.async_default_post_success(
            await response, ignore_error_code=ignore_error_code, expected=expected
        )
        return await response, api_respond_status

    def api_patch_call(
            self, req: str, payload: str, hdr: dict, ) -> requests.models.Response:
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
            return requests.patch(
                req, data=payload,
                verify=self._is_verify_cert,
                headers=headers
            )
        else:
            return requests.patch(
                req, data=payload,
                verify=self._is_verify_cert,
                headers=headers,
                auth=(self._username, self._password)
            )

    async def api_async_patch_call(
            self, loop, req, payload: str, hdr: Dict):
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

    async def api_async_delete_call(
            self, loop, req, payload: str, hdr: Dict):
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

    def read_api_respond(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default success handler,  Check for status code.
        In case of critical error raise exception. If exception expected
        i.e. operation canceled.

        Expected allow to overwrite if API return expect something different
        200, 201, 202, 204

        :param response: requests.models.Response: responses
        :param ignore_error_code: error code to ignore.
        :param expected:  Option status code that we caller consider success.
        :return: IdracApiRespond if httm method request succeed
        :raise RedfishException if HTTP method failed.
        """
        # if location in the header , job created
        print("Response code", response.status_code)

        if response.headers is not None \
                and RedfishJsonSpec.Location in response.headers:
            print("Response code", response.headers[RedfishJsonSpec.Location])
            return IdracApiRespond.AcceptedTaskGenerated

        if response.status_code == expected:
            return self._http_code_mapping[response.status_code]

        if ignore_error_code > 0 and ignore_error_code == response.status_code:
            return self._http_code_mapping[response.status_code]

        if 200 <= response.status_code < 300:
            return self._http_code_mapping[response.status_code]

        self._redfish_error = IDracManager.parse_error(response)
        if 300 <= response.status_code < 500:
            if response.status_code == 400:
                raise RedfishException(self._redfish_error)
            if response.status_code == 401:
                raise RedfishUnauthorized("Authorization failed.")
            if response.status_code == 403:
                raise RedfishForbidden("Authorization failed.")
            if response.status_code == 404:
                raise RedfishForbidden(self._redfish_error)
            return IdracApiRespond.Error
        elif response.status_code >= 500:
            raise RedfishException(
                f"{self._redfish_error.message} HTTP Status code: "
                f"{response.status_code}")
        else:
            raise RedfishException(
                f"{self._redfish_error}, HTTP Status code: "
                f"{response.status_code}"
            )

    def default_patch_success(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 202,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default delete success handler,  Check for status code.
        and raise exception.  Default handler to check post
        request respond.

        :param response: HTTP response
        :param ignore_error_code: error code to ignore.
        :param expected:  Option status code that we caller consider success.
        :return:
        :raise DeleteRequestFailed if POST Method failed
        """
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    def default_post_success(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 200,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    def default_delete_success(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 200,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default delete success handler,  Check for status code.
        and raise exception.  Default handler to check post
        request respond.

        :param response: HTTP response
        :param ignore_error_code: error code to ignore.
        :param expected:  Option status code that we caller consider success.
        :return:
        :raise DeleteRequestFailed if POST Method failed
        """
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    async def async_default_post_success(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default error handler, for post
        :param expected:
        :param response: response HTTP response.
        :param ignore_error_code: ignore HTTP statue error.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    async def async_default_delete_success(
            self,
            response: requests.models.Response,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default error handler, for post
        :param ignore_error_code:
        :param expected:
        :param response: response HTTP response.
        :return: True or False and if failed raise exception
        :raise  PostRequestFailed
        """
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    async def async_default_patch_success(
            self, response: requests.models.Response,
            expected: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> IdracApiRespond:
        """Default error handler for patch http method.
        :param expected:
        :param response: response HTTP response.
        :param ignore_error_code: ignore HTTP statue error.
        :return: True or False and if failed raise exception
        """
        return self.read_api_respond(
            response, expected=expected, ignore_error_code=ignore_error_code
        )

    @staticmethod
    def expanded(level=1):
        """Return prefix to use for expanded respond.
        :param level:
        :return:
        """
        return f"?$expand=*($levels={level})"

    def base_request_respond(
            self,
            resource: str,
            method: HTTPMethod,
            payload: Optional[dict] = None,
            do_async: Optional[bool] = False,
            data_type: Optional[str] = "json",
            expected_status: Optional[int] = 200,
            ignore_error_code: Optional[int] = 0) -> tuple[CommandResult, IdracApiRespond]:
        """A base http patch.

        :param method:
        :param ignore_error_code:
        :param resource:  a request to api,  /redfish/v1/
        :param payload: a json payload
        :param do_async: for asynced request.
        :param data_type: a data-type json/xml
        :param expected_status: expected status code depend on patch msg.
        :return: CommandResult
        """
        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        pd = payload if payload is not None else {}

        self.logger.debug(f"Issuing {method} request to "
                          f"resource: {resource}, "
                          f"payload: {json.dumps(pd)}")

        err = None
        response = None
        api_resp = IdracApiRespond.Error
        try:
            r = f"{self._default_method}{self.idrac_ip}{resource}"
            if not do_async:
                if method == HTTPMethod.PATCH:
                    response = self.api_patch_call(
                        r, json.dumps(pd), headers
                    )
                    api_resp = self.default_patch_success(
                        response, expected=expected_status,
                        ignore_error_code=ignore_error_code
                    )
                if method == HTTPMethod.POST:
                    response = self.api_post_call(
                        r, json.dumps(pd), headers
                    )
                    api_resp = self.default_post_success(
                        response, expected=expected_status,
                        ignore_error_code=ignore_error_code
                    )
                if method == HTTPMethod.DELETE:
                    response = self.api_delete_call(
                        r, headers
                    )
                    api_resp = self.default_delete_success(
                        response, expected=expected_status,
                        ignore_error_code=ignore_error_code
                    )
            else:
                loop = asyncio.get_event_loop()
                if method == HTTPMethod.PATCH:
                    api_resp, response = loop.run_until_complete(
                        self.api_async_patch_until_complete(
                            r, json.dumps(pd), headers,
                            expected=expected_status,
                            ignore_error_code=ignore_error_code
                        )
                    )
                if method == HTTPMethod.POST:
                    api_resp, response = loop.run_until_complete(
                        self.api_async_post_until_complete(
                            r, json.dumps(pd), headers,
                            expected=expected_status,
                            ignore_error_code=ignore_error_code
                        )
                    )
                if method == HTTPMethod.DELETE:
                    api_resp, response = loop.run_until_complete(
                        self.api_async_delete_until_complete(
                            r, json.dumps(pd), headers,
                            expected=expected_status,
                            ignore_error_code=ignore_error_code
                        )
                    )
        except PatchRequestFailed as pf:
            self.logger.critical(
                pf, exc_info=self._is_debug
            )
            err = pf
        except PostRequestFailed as pf:
            self.logger.critical(
                pf, exc_info=self._is_debug
            )
            err = pf
        except DeleteRequestFailed as pf:
            self.logger.critical(
                pf, exc_info=self._is_debug)
            err = pf

        # if task id available we fetch result.
        if api_resp == IdracApiRespond.AcceptedTaskGenerated:
            task_id = self.job_id_from_header(response)
            return CommandResult({"task_id": task_id}, None, response, None), api_resp

        return CommandResult(self.api_success_msg(api_resp), None, None, err), api_resp

    def base_post(self,
                  resource: str,
                  payload: Optional[dict] = None,
                  do_async: Optional[bool] = False,
                  data_type: Optional[str] = "json",
                  expected_status: Optional[int] = 204,
                  ignore_error_code: Optional[int] = 0) -> tuple[CommandResult, IdracApiRespond]:
        """Base http post request for redfish remote api.

        Returns CommandResult and data field contain a data payload.
        If such data is present. In most case post doesn't return anything.

        Method return a tuple CommandResult, IdracApiRespond
        provide option if post accepted , ok status just ok or failed.

        Meanwhile, in case error CommandResult. Error
        store Redfish error if any.

        :param ignore_error_code:
        :param resource: a remote redfish api resource
        :param payload: a json payload
        :param do_async: whether we do asyncio or not
        :param data_type: a default data type json or xml.
        :param expected_status: in case we expect http status that different from spec.
        :return: Tuple[CommandResult, IdracApiRespond]
        :raise: PostRequestFailed for all error that we can't handle.
                i.e. error like api return are not exception.
        """
        return self.base_request_respond(
            resource, HTTPMethod.POST, payload=payload,
            do_async=do_async, data_type=data_type,
            expected_status=expected_status, ignore_error_code=ignore_error_code,
        )

    def base_patch(
            self,
            resource: str,
            payload: Optional[dict] = None,
            do_async: Optional[bool] = False,
            data_type: Optional[str] = "json",
            expected_status: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> tuple[CommandResult, IdracApiRespond]:
        """Base http post request for redfish remote api.

        Returns CommandResult and data field contain a data payload.
        If such data is present. In most case post doesn't return anything.

        Method return a tuple CommandResult, IdracApiRespond
        provide option if post accepted , ok status just ok or failed.

        Meanwhile, in case error CommandResult. Error
        store Redfish error if any.

        :param ignore_error_code:
        :param resource: a remote redfish api resource
        :param payload: a json payload
        :param do_async: whether we do asyncio or not
        :param data_type: a default data type json or xml.
        :param expected_status: in case we expect http status that different from spec.
        :return: Tuple[CommandResult, IdracApiRespond]
        :raise: PostRequestFailed for all error that we can't handle.
                i.e. error like api return are not exception.
        """
        return self.base_request_respond(
            resource, HTTPMethod.PATCH, payload=payload,
            do_async=do_async, data_type=data_type,
            expected_status=expected_status, ignore_error_code=ignore_error_code,
        )

    def base_delete(
            self,
            resource: str,
            payload: Optional[dict] = None,
            do_async: Optional[bool] = False,
            data_type: Optional[str] = "json",
            expected_status: Optional[int] = 204,
            ignore_error_code: Optional[int] = 0) -> tuple[CommandResult, IdracApiRespond]:
        """Base http delete request for redfish remote api.

        Returns CommandResult and data field contain a data payload.
        If such data is present. In most case post doesn't return anything.

        Method return a tuple CommandResult, IdracApiRespond
        provide option if post accepted , ok status just ok or failed.

        Meanwhile, in case error CommandResult. Error
        store Redfish error if any.

        :param ignore_error_code:
        :param resource: a remote redfish api resource
        :param payload: a json payload
        :param do_async: whether we do asyncio or not
        :param data_type: a default data type json or xml.
        :param expected_status: in case we expect http status that different from spec.
        :return: Tuple[CommandResult, IdracApiRespond]
        :raise: PostRequestFailed for all error that we can't handle.
                i.e. error like api return are not exception.
        """
        return self.base_request_respond(
            resource, HTTPMethod.DELETE, payload=payload,
            do_async=do_async, data_type=data_type,
            expected_status=expected_status, ignore_error_code=ignore_error_code,
        )

    def reboot(
            self,
            do_watch: Optional[bool] = False,
            power_state_attr: Optional[str] = "PowerState",
            default_reboot_type: Optional[ResetType] = ResetType.ForceRestart.value) -> CommandResult:
        """Reboot a chassis, if chassis in power down state.

        Reboot on power down state is no op, method return
        chassis data. caller need check CommandResult data
        and if required Change power state.

        :param do_watch: if reboot respond with task_id, do watch
                         passed to reboot and block reboot complete.
        :param default_reboot_type: ResetType.ForceRestart: type reboot.
        :param power_state_attr:  is attribute method check
                to determine chassis up or in power done state.
        :return:
        """
        # state of chassis
        cmd_chassis = self.sync_invoke(
            ApiRequestType.ChassisQuery,
            "chassis_service_query",
            data_filter=power_state_attr
        )

        if cmd_chassis.error is not None:
            self.logger.info(
                f"Failed to fetch a chassis power state. Chassis return error."
            )
            return cmd_chassis

        if isinstance(cmd_chassis.data, dict) and IDRAC_JSON.PowerState in cmd_chassis.data:
            pd_state = cmd_chassis.data[power_state_attr]
            if pd_state.lower() == 'on':
                return self.sync_invoke(
                    ApiRequestType.ComputerSystemReset, "reboot",
                    reset_type=default_reboot_type,
                    do_wait=do_watch
                )
            else:
                self.logger.info(
                    f"Can't reboot a host, "
                    f"chassis power state in {pd_state} state."
                )
                return CommandResult({}, None, None, None)
        else:
            self.logger.info(
                f"Failed to acquire current power state."
            )

        return cmd_chassis

    @cached_property
    def idrac_firmware(self) -> str:
        """Shared method return idrac firmware
        :return: str: firmware.
        """
        api_return = self.base_query(self.idrac_members,
                                     key=IDRAC_JSON.FirmwareVersion)
        return api_return.data

    def idrac_last_reset(self) -> datetime:
        """Shared method returns idrac last reset time as datatime
        :return: datetime
        """
        idrac_reset_time = None
        api_return = self.base_query(self.idrac_members,
                                     key=IDRAC_JSON.LastResetTime)
        try:
            idrac_reset_time = datetime.fromisoformat(api_return.data)
        except ValueError as ve:
            self.logger.error(ve)
        return idrac_reset_time

    def idrac_current_time(self) -> datetime:
        """Shared method return idrac current time, if idrac
        return none ISO format
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
        """return local time in iso format
        :return: idrac local time
        """
        current_date = datetime.now()
        return current_date.isoformat()

    def idrac_time_offset(self):
        """
        :return:  idrac time zone
        """
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
    def idrac_managers_count(self) -> str:
        """Return manager count. typically it 1
        :return:
        """
        cmd_result = self.base_query(f"{IDRAC_API.IDRAC_MANAGER}")
        return cmd_result.data["Members@odata.count"]

    @cached_property
    def idrac_manager_version(self) -> str:
        """Remote idrac version.
        :return:
        """
        cmd_result = self.base_query(
            f"{IDRAC_API.IDRAC_MANAGER}", key=IDRAC_JSON.Members)

        # idrac ctl only manage one instance.
        member_list = cmd_result.data
        if len(member_list) > 1:
            logging.warning("idrac manage more than one entity")
        elif len(member_list) == 1:
            member = member_list[-1]
            if RedfishJson.Data_id in member:
                member_target = member[RedfishJson.Data_id]
                cmd_result = self.base_query(
                    member_target,
                    key=IDRAC_JSON.IDracFirmwareVersion
                )
                return cmd_result.data
        else:
            raise

    @cached_property
    def idrac_members(self) -> str:
        """Shared method return idrac manage members servers list as json
        /redfish/v1/Managers/iDRAC.Embedded.1

        Upon first call , result cached all follow-up call will return cached result.
        :return:
        """
        cmd_result = self.base_query(f"{IDRAC_API.IDRAC_MANAGER}", key=IDRAC_JSON.Members)
        return self.value_from_json_list(cmd_result.data, IDRAC_JSON.Data_id)

    @cached_property
    def idrac_members(self) -> str:
        """Shared method return idrac manage members servers list as json
        /redfish/v1/Managers/iDRAC.Embedded.1
        after first cal , result cached all follow-up call will return cached result.
        :return:
        """
        cmd_result = self.base_query(f"{IDRAC_API.IDRAC_MANAGER}", key=IDRAC_JSON.Members)
        return self.value_from_json_list(cmd_result.data, IDRAC_JSON.Data_id)

    def computer_system_id(self):
        """alias name for idrac_manage_servers to match v6.0 docs
        :return: str: computer_system_id "/redfish/v1/Systems/System.Embedded.1"
        """
        return self.idrac_manage_servers

    @cached_property
    def idrac_manage_servers(self) -> str:
        """Shared method return idrac managed servers list as json
        list i.e. /redfish/v1/Systems/System.Embedded.1
        after first cal , result cached all follow-up call will return cached result.
        :return:
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
        """Shared method return idrac id, i.e. System.Embedded.1
        id cached all follow-up calls and will return cached result.
        :return:
        """
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
        """
        This idrac_ctl optional parser for all sub command
        that most of command share.
        Each sub-command can add additional optional flags and args.
        :param is_async: will add to optional group async
        :param is_file_save:  will add to optional group arg option save to file
        :param is_expanded:  will add to optional group arg option for expanded query
        :param is_remote_share:  will add remote share for optional group arg
        :param is_reboot:  will add optional reboot for optional arg.
                           ( for cmds that we want to execute and reboot)
        :return:
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
    def schedule_job_request(
            reboot_type: ScheduleJobType,
            start_time_isofmt: Optional[str],
            duration_time: Optional[int]) -> dict:
        """Create a JSON payload for schedule a job, either
        somewhere in future or OnReset.

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

    @staticmethod
    def make_future_job_ts(start_date: str,
                           start_time: str,
                           is_json_string=False) -> str:
        """Make a future time for a maintenance task.

        Specifically @Redfish.MaintenanceWindow

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
        The settings apply time and operation apply time annotations
        enable an operation to be performed during a maintenance window
        :param start_date a date as string
        :param start_time a start time for a future job
        :param default_duration a duration
        :param apply time auto-boot, maintenance, on-reset
        :raise InvalidArgumentFormat will raise in case we can't parse args
        :raise ValueError if unknown apply type
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

    def api_success_msg(self,
                        api_respond: IdracApiRespond,
                        message_key: Optional[str] = "message",
                        message=None) -> Dict:
        """A default api success respond,
        Return dict contains Status, and it describes whether rest return
        ok, accepted or success.

        if message and msg key provide msg key added to a dict.
        for example if we want to add extra information about success.

        :param api_respond: respond enum. we report to upper ok, accepted, success.
        :param message_key: key we need add extra
        :param message: message information data
        :return: a dict
        """
        return_dict = {
            "Status": self._api_respond_to_string[api_respond]
        }

        if message is not None:
            return_dict[message_key] = message

        return return_dict

    @property
    def power_state(self) -> PowerState:
        """
        :return:
        """
        cmd_result = self.base_query(self.idrac_manage_chassis,
                                     do_async=False,
                                     do_expanded=True)

        if cmd_result.error is not None:
            return PowerState.Unknown

        if IDRAC_JSON.PowerState not in cmd_result.data:
            raise UnexpectedResponse(f"{IDRAC_JSON.PowerState} not present in respond.")

        power_state = cmd_result.data[IDRAC_JSON.PowerState]
        if 'On' in power_state:
            return PowerState.On
        if 'Off' in power_state:
            return PowerState.Off

    def chassis_string_property(self, property_name: str) -> str:
        """ Return chassis string property
        :param property_name:
        :return:
        """
        cmd_result = self.base_query(self.idrac_manage_chassis,
                                     do_async=False,
                                     do_expanded=True)

        if property_name not in cmd_result.data:
            raise UnexpectedResponse(f"{property_name} not present in respond.")

        json_property = cmd_result.data[property_name]
        if not isinstance(json_property, str):
            raise UnexpectedResponse(f"{property_name} must be a string.")

        return cmd_result.data[property_name]

    @cached_property
    def serial(self) -> str:
        """return chassis serial number
        :return: str: chassis serial number
        """
        return self.chassis_string_property("SerialNumber")

    @cached_property
    def chassis_type(self) -> str:
        """return chassis type
        :return: str: chassis type
        """
        return self.chassis_string_property("ChassisType")

    @cached_property
    def chassis_uuid(self) -> str:
        """return chassis uuid
        :return: str: chassis uuid
        """
        return self.chassis_string_property("UUID")
