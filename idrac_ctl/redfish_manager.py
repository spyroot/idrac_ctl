"""Redfish implementation based
on redfish specification.

https://www.dmtf.org/standards/REDFISH

Author Mus spyroot@gmail.com
"""

import asyncio
import collections
import functools
import logging
import re
from abc import abstractmethod
from functools import cached_property
from typing import Optional, Dict

import requests

from .redfish_shared import RedfishApi, RedfishJsonMessage
from .redfish_shared import RedfishApiRespond
from .redfish_shared import RedfishJsonSpec

from .cmd_exceptions import AuthenticationFailed
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import TaskIdUnavailable
from .cmd_utils import save_if_needed
from .redfish_respond import RedfishRespondMessage
from .redfish_respond_error import RedfishError

from .redfish_exceptions import RedfishForbidden
from .redfish_exceptions import RedfishMethodNotAllowed
from .redfish_exceptions import RedfishNotAcceptable
from .redfish_exceptions import RedfishUnauthorized
from .redfish_shared import RedfishJson

"""Each command encapsulate result in named tuple"""
CommandResult = collections.namedtuple("cmd_result",
                                       ("data", "discovered", "extra", "error"))


class RedfishManager:

    def __init__(self,
                 redfish_ip: Optional[str] = "",
                 redfish_username: Optional[str] = "root",
                 redfish_password: Optional[str] = "",
                 redfish_port: Optional[int] = 443,
                 insecure: Optional[bool] = False,
                 is_http: Optional[bool] = False,
                 x_auth: Optional[str] = None,
                 is_debug: Optional[bool] = False):
        """Default constructor for Redfish Manager.
           it requires a credentials to interact with redfish endpoint.
           By default, Redfish Manager uses json to serialize a data to callee
           and uses json content type.

        :param redfish_ip: redfish IP or hostname
        :param redfish_username: redfish username default is root
        :param redfish_password: redfish password.
        :param insecure: by default, we use insecure SSLself.api_success_msg(api_resp)
        :param x_auth: X-Authentication header.
        """
        self._redfish_ip = redfish_ip
        self._username = redfish_username
        self._password = redfish_password

        if isinstance(redfish_port, str):
            redfish_port = int(redfish_port)

        self._port = redfish_port
        self._is_verify_cert = insecure
        self._x_auth = x_auth
        self._is_debug = is_debug
        self._is_http = is_http
        self._default_method = "https://"
        if self._is_http:
            self._default_method = "http://"

        self.logger = logging.getLogger(__name__)

        self.content_type = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        self.json_content_type = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        self._manage_servers_obs = []
        self._manage_chassis_obs = []
        # mainly to track query sent , for unit test
        self.query_counter = 0
        # run time
        self.action_targets = None
        self.api_endpoints = None

    @property
    def redfish_ip(self) -> str:
        if ":" in self._redfish_ip:
            return self._redfish_ip
        else:
            if self._port != 443:
                return f"{self._redfish_ip}:{self._port}"
            else:
                return self._redfish_ip

    @property
    def username(self) -> str:
        return self._username

    @property
    def password(self) -> str:
        return self._password

    @property
    def x_auth(self) -> str:
        return self._x_auth

    def authentication_header(self):
        pass

    @staticmethod
    def redfish_error_handlers(status_code):
        if status_code == 401:
            raise AuthenticationFailed(
                "Authentication failed."
            )
        if status_code == 403:
            raise RedfishForbidden(
                "Authentication failed."
            )
        if status_code == 403:
            raise RedfishForbidden(
                "Authentication failed."
            )
        if status_code == 405:
            raise RedfishMethodNotAllowed(
                "DELETE, GET, HEAD, POST, PUT, "
                "or PATCH , is not supported."
            )
        if status_code == 406:
            raise RedfishNotAcceptable(
                "Server rejected error code 406."
            )
        if status_code == 409:
            raise RedfishNotAcceptable(
                "Creation or update request could not be completed "
                "because it would cause a conflict "
                "in the current state of the resources."
            )

    @staticmethod
    async def async_default_error_handler(
            response: requests.models.Response) -> bool:
        """Default error handler for base query and redfish error code based on spec.
        :param response:
        :return:
        """
        if response.status_code >= 200 or response.status_code < 300:
            return True
        RedfishManager.redfish_error_handlers(response.status_code)

    async def api_async_get_call(self, loop, req, hdr: Dict):
        """Make api request either with x-auth authentication header or base authentication
        to redfish endpoint.

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

    def api_get_call(
            self, req: str, hdr: Dict) -> requests.models.Response:
        """Make api request either with x-auth authentication
        header or base authentication to redfish.
        :param req:  request
        :param hdr: http header dict that will append to HTTP/HTTPS request.
        :return: request.
        """
        headers = {}
        headers.update(self.content_type)
        if hdr is not None:
            headers.update(hdr)

        if self._x_auth is not None:
            headers.update(
                {
                    'X-Auth-Token': self._x_auth
                }
            )
            return requests.get(
                req, verify=self._is_verify_cert, headers=headers
            )
        else:
            return requests.get(
                req, verify=self._is_verify_cert,
                auth=(self._username, self._password)
            )

    @staticmethod
    def expanded(level: Optional[int] = 1):
        """Return prefix to use for expanded respond.

         * Shall expand all hyperlinks, including those in

         * Number of levels the service should cascade the $expand operation.

         * . Shall expand all hyperlinks not in any links property instances of the resource,
             including those in payload annotations, such as @Redfish.Settings ,
             @Redfish.ActionInfo , and @Redfish.CollectionCapabilities .

         * ~ Shall expand all hyperlinks found in all links property instances of the resource.
        :param level:
        :return:
        """
        return f"?$expand=*($levels={level})"

    async def api_async_get_until_complete(self, req: str, hdr: Dict, loop=None):
        """Execute async get request
        :param req: api method caller request.
        :param hdr: dict: http/https header
        :param loop:  asyncio loop
        :return: http response object
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_get_call(loop, req, hdr)
        await self.async_default_error_handler(await response)
        return await response

    @cached_property
    def redfish_version(self) -> str:
        """Return version remote endpoint implemented
        :return:
        """
        api_resp = self.base_query("/redfish/v1/")
        if api_resp.data is not None and "RedfishVersion" in api_resp.data:
            return api_resp.data["RedfishVersion"]
        return ""

    @cached_property
    def redfish_vendor(self) -> str:
        """Return remote vendor
        :return:
        """
        api_resp = self.base_query("/redfish/v1/")
        if api_resp.data is not None and "Vendor" in api_resp.data:
            return api_resp.data["Vendor"]
        return ""

    @cached_property
    def redfish_system(self) -> str:
        """Return system path
        :return:
        """
        api_resp = self.base_query("/redfish/v1/")
        if api_resp.data is not None and "Systems" in api_resp.data:
            return api_resp.data["Systems"]["@odata.id"]
        return ""

    @staticmethod
    def select(select_property: Optional[str] = "") -> str:
        """Return true if IDRAC version 6.0 i.e. a new version.
        :return:
        """
        return f"?$select={select_property}"

    def base_query(self,
                   resource: str,
                   filename: Optional[str] = None,
                   do_async: Optional[bool] = False,
                   do_expanded: Optional[bool] = False,
                   select_target: Optional[str] = "",
                   query_expansion: Optional[str] = "",
                   data_type: Optional[str] = "json",
                   verbose: Optional[bool] = False,
                   key: Optional[str] = None,
                   **kwargs) -> CommandResult:
        """A base implementation for query redfish. This method shared
        by many other methods that require just a base http get query.

        do_expanded allow to leverage  $expand query parameter and
        enables a client to request a response that includes not only the
        requested resource, but also includes the contents of the
        subordinate or hyperlinked resource.

        Note tht expanded usually very chatty.

        By default,  base_query uses ?$expand=*($levels={level}

        :param select_target: select particular attribute
        :param resource: path to a redfish resource
        :param do_async: sync will subscribe to an event loop and issue async request.
        :param do_expanded:  will do expand query based on spec.
        :param query_expansion:  allow to overwrite expansion, and it always appended to request.
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output, mainly to debug if endpoint return something strange.
        :param data_type: json or xml
        :param key: Optional json key in case we want to get something from a root element only.
        :return: CommandResult
        :raise RedfishException
        """
        if verbose:
            self.logger.debug(
                f"base_query received args"
                f"data_type: {data_type} "
                f"resource: {resource} "
                f"do_expanded:{do_expanded} "
                f"do_async: {do_async} "
                f"filename: {filename}")
            self.logger.debug(f"the rest of args: {kwargs}")

        headers = {}
        if data_type == "json":
            headers.update(self.json_content_type)

        # for expanded
        if len(query_expansion) > 0:
            r = f"{self._default_method}{self.redfish_ip}{resource}{self.expanded()}"
        elif do_expanded:
            r = f"{self._default_method}{self.redfish_ip}{resource}{self.expanded()}"
        else:
            r = f"{self._default_method}{self.redfish_ip}{resource}"

        if len(select_target) > 0:
            r = f"{self._default_method}{self.redfish_ip}" \
                f"{resource}{self.select(select_property=select_target)}"

        logging.debug(f"Sending request to {r}")

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

    @staticmethod
    def parse_error(error_response: requests.models.Response) -> RedfishError:
        """Default Parser for error msg from a JSON error.
        Note that respond can be same as success msg.

        :param error_response:
        :return:
        """
        redfish_error = RedfishError(error_response.status_code)

        try:
            err_resp = error_response.json()
            if 'error' not in err_resp:
                return err_resp

            err_data = err_resp['error']
            # on top of redfish error we copy status code and header
            # if we need analyze verbose error
            redfish_error = RedfishError(error_response.status_code)

            if 'message' in err_data:
                redfish_error.message = err_data['message']

            if RedfishJsonMessage.MessageExtendedInfo in err_data:
                message_extended = err_data[RedfishJsonMessage.MessageExtendedInfo]
                if isinstance(message_extended, list):
                    redfish_error.message_extended = [
                        m for m in message_extended if isinstance(m, dict)
                    ]
        except requests.exceptions.JSONDecodeError as json_err:
            redfish_error.exception_msg = str(json_err)
            return redfish_error

        return redfish_error

    @staticmethod
    def parse_json_respond_msg(
            resp: requests.models.Response) -> RedfishRespondMessage:
        """Default parser for json respond. For example if HTTP post or HTTP Delete
        return payload

        :param resp: requests.models.Response
        :return:
        """
        redfish_resp = RedfishRespondMessage(resp.status_code)
        try:
            json_data = resp.json()
            if RedfishJsonMessage.MessageExtendedInfo in json_data:
                redfish_resp.message_extended = [
                    m for m
                    in json_data[RedfishJsonMessage.MessageExtendedInfo]
                ]
        except requests.exceptions.JSONDecodeError as _:
            pass
        except TypeError as _:
            pass

        finally:
            return redfish_resp

    @staticmethod
    def default_error_handler(response) -> RedfishApiRespond:
        """Default error handler.
        :param response:
        :return:
        """
        if response.status_code == 200:
            return RedfishApiRespond.Ok
        if response.status_code == 202:
            return RedfishApiRespond.AcceptedTaskGenerated
        if response.status_code == 204:
            return RedfishApiRespond.Success
        if response.status_code >= 200 or response.status_code < 300:
            return RedfishApiRespond.Success
        if response.status_code == 401:
            raise RedfishUnauthorized("Unauthorized access")
        elif response.status_code == 403:
            raise RedfishForbidden("access forbidden")
        elif response.status_code == 404:
            error_msg = RedfishManager.parse_error(response)
            raise ResourceNotFound(error_msg)
        else:
            error_msg = RedfishManager.parse_error(response)
            raise ResourceNotFound(error_msg)

    @staticmethod
    def value_from_json_list(json_obj, k: str):
        """Try to parse the JSON object and get the key. It doesn't do a deep lookup.
        If an object is a list, it attempts to get a key. Note this specifically for cases
        When spec defines an array, but a list holds a single element.

        :param json_obj: could be a list , dict or string.
        :param k: a key
        :return: a value or None
        """
        # a case for list, return last
        if isinstance(json_obj, list) and len(json_obj) > 0:
            list_flat = json_obj[-1]
            if isinstance(list_flat, dict):
                if k in list_flat:
                    return list_flat[k]
        # a case for dict
        elif isinstance(json_obj, dict):
            if k in json_obj:
                return json_obj[k]
        # a case for str
        elif isinstance(json_obj, str):
            return json_obj
        else:
            return None

    @cached_property
    def members(self):
        """Redfish manager members.
        :return:
        """
        cmd_result = self.base_query(f"{RedfishApi.Managers}", key=RedfishJson.Members)
        return self.value_from_json_list(cmd_result.data, RedfishJson.Data_id)

    @abstractmethod
    def redfish_manage_servers(self) -> str:
        """Shared method return who remote endpoint managed servers
        and list as json ManagerForServers
        :return: return manager
        """
        api_resp = self.base_query(self.members, key=RedfishJson.Links)
        if api_resp.data is not None and RedfishJson.ManagerServers in api_resp.data:
            if isinstance(api_resp.data, dict):
                manage_servers = api_resp.data[RedfishJson.ManagerServers]
                self._manage_servers_obs = manage_servers
                return self.value_from_json_list(
                    manage_servers, RedfishJson.Data_id
                )
        else:
            self.logger.error("")
        return ""

    @staticmethod
    def job_id_from_header(
            response: requests.models.Response,
            strict: Optional[bool] = True) -> str:
        """Returns job id from the response header.
        :param strict: if true will raise exception.
        :param response: a response that should have job id information in the header.
        :return: job id from the Location header
        :raise TaskIdUnavailable if header not present.
        """
        job_id = ""
        resp_hdr = response.headers
        if RedfishJsonSpec.Location not in resp_hdr:
            if strict:
                raise TaskIdUnavailable(
                    "There is no location in the response header. "
                    "(not all api create job id)"
                )
        else:
            location = response.headers[RedfishJsonSpec.Location]
            job_id = location.split("/")[-1]

        return job_id

    @staticmethod
    def job_id_from_respond(
            response: requests.models.Response) -> str:
        """Try to parse job id from HTTP respond, otherwise empty string
        :param response: requests.models.Response
        :return: str: a job id or empty string
        """
        try:
            if response is not None and hasattr(response, __dict__):
                response_dict = str(response.__dict__)
                if response_dict is not None and len(response_dict) > 0:
                    job_id = re.search("JID_.+?,", response_dict)
                    if job_id is not None:
                        job_id = job_id.group(0)
                    return job_id
        except AttributeError as _:
            pass

        return ""

    def parse_task_id(self, data) -> str:
        """Parses input data and try to get a
        job id from the http header or http response.

        :param data:  http response or CommandResult
        :return: job_id or empty string.
        """
        # get response from extra
        if data is None:
            return ""

        # TODO this case I need remove
        if hasattr(data, "extra"):
            resp = data.extra
        elif isinstance(data, requests.models.Response):
            resp = data
        else:
            raise ValueError("Unknown data type.")

        if resp is None:
            return ""

        # this based on spec
        try:
            job_id = self.job_id_from_header(resp)
            logging.debug(f"idrac api returned job_id: {job_id} in the response header.")
            return job_id
        # ignored.
        except TaskIdUnavailable as _:
            pass

        # this from response
        try:
            # try to get from the response, it an optional check.
            job_id = self.job_id_from_respond(resp)
            logging.debug(f"idrac api returned job_id: {job_id} in the response header.")
        except TaskIdUnavailable as _:
            pass

        return ""

    @abstractmethod
    def api_success_msg(self,
                        api_respond: RedfishApiRespond,
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
        pass
