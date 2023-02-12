"""Redfish implementation based
on redfish specification.

https://www.dmtf.org/standards/REDFISH

Author Mus spyroot@gmail.com
"""


import asyncio
import collections
import functools
import logging
from abc import abstractmethod
from functools import cached_property
from typing import Optional, Dict

import requests

from .cmd_exceptions import AuthenticationFailed, RedfishMethodNotAllowed
from .cmd_exceptions import ResourceNotFound
from .cmd_exceptions import UnexpectedResponse
from .shared import RedfishApi, RedfishJson
from .cmd_utils import save_if_needed

"""Each command encapsulate result in named tuple"""
CommandResult = collections.namedtuple("cmd_result",
                                       ("data", "discovered", "extra", "error"))


class RedfishManager:

    def __init__(self,
                 redfish_ip: Optional[str] = "",
                 redfish_username: Optional[str] = "root",
                 redfish_password: Optional[str] = "",
                 insecure: Optional[bool] = False,
                 x_auth: Optional[str] = None,
                 is_debug: Optional[bool] = False):
        """Default constructor for Redfish Manager.
           it requires a credentials to interact with redfish endpoint.
           By default, Redfish Manager uses json to serialize a data to callee
           and uses json content type.

        :param redfish_ip: redfish IP address
        :param redfish_username: redfish username default is root
        :param redfish_password: redfish password.
        :param insecure: by default, we use insecure SSL
        :param x_auth: X-Authentication header.
        """
        self._redfish_ip = redfish_ip
        self._username = redfish_username
        self._password = redfish_password
        self._is_verify_cert = insecure
        self._x_auth = x_auth
        self._is_debug = is_debug
        self._default_method = "https://"
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
    async def async_default_error_handler(
            response: requests.models.Response) -> bool:
        """Default error handler for base query type of request.
        :param response:
        :return:
        """
        if response.status_code >= 200 or response.status_code < 300:
            return True

        if response.status_code == 401:
            raise AuthenticationFailed(
                "Authentication failed."
            )
        if response.status_code == 403:
            raise AuthenticationFailed(
                "Authentication failed."
            )

        if response.status_code == 405:
            raise RedfishMethodNotAllowed(
                "Authentication failed."
            )

        if response.status_code == 405:
            raise AuthenticationFailed(
                "Authentication failed."
            )

        if response.status_code != 200:
            raise UnexpectedResponse(
                f"Failed acquire result. "
                f"Status code {response.status_code}"
            )

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

    async def api_async_get_until_complete(self, r: str, hdr: Dict, loop=None):
        """
        :param r:
        :param hdr: http header
        :param loop:  asyncio loop
        :return:
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        response = await self.api_async_get_call(loop, r, hdr)
        await self.async_default_error_handler(await response)
        return await response

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
            r = f"{self._default_method}{self._redfish_ip}{resource}{self.expanded()}"
        else:
            r = f"{self._default_method}{self._redfish_ip}{resource}"

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

    @abstractmethod
    def parse_error(self):

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
            error_msg, json_error = RedfishManager.parse_error(response)
            raise ResourceNotFound(error_msg)
        return False

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
    def members(self):
        cmd_result = self.base_query(f"{RedfishApi.Managers}", key=RedfishJson.Members)
        return self.value_from_json_list(cmd_result.data, RedfishJson.Data_id)

    @abstractmethod
    def redfish_manage_servers(self) -> str:
        """Shared method return idrac managed servers list as json
        "/redfish/v1/Systems/System.Embedded.1"
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
