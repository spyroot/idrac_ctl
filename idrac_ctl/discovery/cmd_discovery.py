"""Redfish discovery command

Command discover all idrac / redfish resources.

Author Mus spyroot@gmail.com
"""
import json
import os
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from ..idrac_manager import IDracManager
from ..idrac_shared import ApiRequestType, Singleton
from ..redfish_exceptions import RedfishForbidden
from ..redfish_manager import CommandResult

# Upper bound on how deep recursive_discovery will walk below a top-level
# resource. Real Redfish trees are far shallower than this; the bound exists
# purely to guarantee termination even if normalization/dedup ever misses a
# cyclic back-reference.
DEFAULT_DISCOVERY_MAX_DEPTH = 32


class Discovery(IDracManager,
                scm_type=ApiRequestType.Discovery,
                name='discovery',
                metaclass=Singleton):
    """A command discovery all redfish resource  based on a resource path
    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(Discovery, self).__init__(*args, **kwargs)
        self._discovered_url_file_mapping = {}
        self._api_allowed_methods = {}

        self.visited_urls = {}
        home_dir = str(Path.home())
        redfish_ip = self.redfish_ip.replace(":", "")
        self.json_response_dir = f"{str(home_dir)}/.json_responses/{redfish_ip}"

        # default filter that will skip these entities.
        self.default_query_filter = [
            "LogServices/Sel/Entries",
            "JID_",
            "StdSecbootpolicy.",
            "Signatures/StdSecbootpolicy.",
            "Lclog/Entries/"]

    @staticmethod
    @abstractmethod
    def register_subcommand(cls):
        """Register command and all optional flags.
        :param cls:
        :return:
        """
        cmd_parser = cls.base_parser()
        help_text = "command discovery all action."
        return cmd_parser, "discovery", help_text

    def extract_odata_ids(self, data):
        """Extract odata ids
        :param data:
        :return:
        """
        if isinstance(data, dict):
            odata_id = data.get("@odata.id")
            if odata_id:
                yield odata_id
            uri = data.get("Uri")
            if uri:
                print("Found uri")
                yield uri
            # target = data.get("@target")
            # print(target)
            for value in data.values():
                yield from self.extract_odata_ids(value)
        elif isinstance(data, list):
            for item in data:
                yield from self.extract_odata_ids(item)

    @staticmethod
    def normalize_resource_path(resource_path: str) -> str:
        """Canonicalize a Redfish resource path so URI variants map to one key.

        Redfish hands back the same logical resource under several spellings:
        a trailing slash (``.../Managers/``), a query string from an ``$expand``
        / ``$select`` / ``$ref`` request, or duplicate slashes from a naive
        string join (``/redfish//v1``). Keying ``visited_urls`` on the raw
        string would treat each spelling as a new resource and re-walk it, so we
        collapse them to a single canonical form first.

        :param resource_path: a raw ``@odata.id`` / ``Uri`` value
        :return: the path with any query string dropped, duplicate slashes
                 collapsed, and a trailing slash removed (never reduced to "")
        """
        if not resource_path:
            return resource_path
        # Drop any query string ($expand, $select, $ref, odata.id fragments...).
        path = resource_path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        # Collapse duplicate slashes ("/redfish//v1/Managers" -> "/redfish/v1/Managers").
        while "//" in path:
            path = path.replace("//", "/")
        # Strip trailing slash(es), but never collapse the path away entirely.
        if len(path) > 1:
            path = path.rstrip("/") or path
        return path

    def recursive_discovery(self,
                            resource_path,
                            depth: int = 0,
                            max_depth: int = DEFAULT_DISCOVERY_MAX_DEPTH):
        """Recursively walk and discover Redfish resources from ``resource_path``.

        URI variants of the same resource (trailing slash, query string,
        duplicate slashes) are normalized to one key before the visited check,
        so each logical resource is fetched exactly once. Recursion stops once
        ``depth`` exceeds ``max_depth`` so a missed back-reference can never spin
        forever.

        :param resource_path: a Redfish resource path (raw ``@odata.id``)
        :param depth: current recursion depth; callers start at 0
        :param max_depth: maximum depth to walk below the starting resource
        :return:
        """
        if depth > max_depth:
            return

        resource_path = self.normalize_resource_path(resource_path)

        for query_filter in self.default_query_filter:
            if query_filter in resource_path:
                self.visited_urls[resource_path] = True
                return

        if resource_path in self.visited_urls or not resource_path.startswith("/redfish/v1"):
            return

        try:
            result = self.base_query(resource_path)
            allow_header = result.extra
            if allow_header is not None:
                allowed_methods = [method.strip() for method in allow_header.split(",")]
            else:
                allowed_methods = []

            print("Discovery: {} {}".format(resource_path, allowed_methods))

            self.visited_urls[resource_path] = True
            response_filename = os.path.join(
                self.json_response_dir, resource_path.replace("/", "_") + ".json")

            with open(response_filename, "w") as file:
                json.dump(result.data, file, indent=4)

            self._discovered_url_file_mapping[resource_path] = response_filename
            self._api_allowed_methods[resource_path] = allowed_methods

            odata_ids = list(self.extract_odata_ids(result.data))

            for r in odata_ids:
                self.recursive_discovery(r, depth + 1, max_depth)
        except RedfishForbidden as e:
            self.visited_urls[resource_path] = True
            print("Forbidden: {}".format(e))
        except Exception as other_err:
            self.visited_urls[resource_path] = True
            print("Discovery error at {}: {}".format(resource_path, other_err))

    def save_url_file_mapping(self):
        """Save the URL-to-file mapping to a JSON respond file
        and what each api allow.

        numpy is imported lazily here so importing this module does not
        require numpy to be installed; it is only needed for ``np.save``.
        """
        import numpy as np

        filename = os.path.join(self.json_response_dir, "rest_api_map.npy")
        mappings = {
            "url_file_mapping": self._discovered_url_file_mapping,
            "allowed_methods_mapping": self._api_allowed_methods
        }
        filename = os.path.join(self.json_response_dir, filename)
        np.save(filename, mappings)

    def execute(self,
                filename: Optional[str] = None,
                data_type: Optional[str] = "json",
                verbose: Optional[bool] = False,
                do_async: Optional[bool] = False,
                do_expanded: Optional[bool] = False,
                **kwargs) -> CommandResult:
        """Executes discovery action command
        python idrac_ctl discovery

        :param do_async: note async will subscribe to an event loop.
        :param do_expanded:  will do expand query
        :param filename: if filename indicate call will save a bios setting to a file.
        :param verbose: enables verbose output
        :param data_type: json or xml
        :return: CommandResult and if filename provide will save to a file.
        """

        os.makedirs(self.json_response_dir, exist_ok=True)
        if not os.path.isdir(self.json_response_dir):
            raise ValueError("Failed to create directory: {}".format(self.json_response_dir))

        result = self.base_query("/redfish/v1/",
                                 filename=filename,
                                 do_async=do_async,
                                 do_expanded=do_expanded)

        # Seed normalized keys so a child link back to the root (e.g. the
        # bare "/redfish/v1") matches and is not re-walked.
        self.visited_urls[self.normalize_resource_path("/redfish/v1/")] = True
        self.visited_urls[self.normalize_resource_path("/redfish/v1/CompositionService")] = True
        odata_ids = list(self.extract_odata_ids(result.data))
        for r in odata_ids:
            self.recursive_discovery(r)
        self.save_url_file_mapping()
        return result
