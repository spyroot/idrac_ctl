"""Validate Redfish JSON against the DMTF DSP8010 schemas.

Maps a resource's ``@odata.type`` to its unversioned (version-resilient) JSON
Schema and validates it with ``jsonschema`` + ``referencing``. Schema files are
cached under ``tools/redfish-schemas/``; a missing one is fetched once from
``redfish.dmtf.org`` and cached for offline reuse. Set ``REDFISH_SCHEMA_OFFLINE=1``
to forbid network and require a pre-vendored directory.

Dell ``Oem`` blocks are not part of the standard schema, so by default the ``Oem``
subtree is stripped before validation — we check the standard surface, not Dell's
private extensions. Resources whose ``@odata.type`` is itself an OEM type (e.g.
``#DellBootSources...``) have no standard schema and raise ``SchemaUnavailable``.

Author Mus spyroot@gmail.com
"""
import json
import os
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT7

SCHEMA_DIR = Path(__file__).resolve().parent / "redfish-schemas"
PREFIX = "http://redfish.dmtf.org/schemas/v1/"


class SchemaUnavailable(RuntimeError):
    """The schema for a resource could not be found (OEM type, or offline+missing)."""


def _schema_file(uri: str) -> Path:
    name = uri[len(PREFIX):] if uri.startswith(PREFIX) else Path(uri).name
    return SCHEMA_DIR / name.split("#", 1)[0]


def _load_schema_doc(uri: str) -> dict:
    path = _schema_file(uri)
    if path.exists():
        return json.loads(path.read_text())
    if os.environ.get("REDFISH_SCHEMA_OFFLINE"):
        raise SchemaUnavailable(f"missing vendored schema for {uri} (offline mode)")
    url = uri.split("#", 1)[0]
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
    except urllib.error.HTTPError as err:
        raise SchemaUnavailable(f"no standard schema at {url} ({err.code})") from err
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return json.loads(data)


def _retrieve(uri: str) -> Resource:
    return Resource.from_contents(_load_schema_doc(uri), default_specification=DRAFT7)


_REGISTRY = Registry(retrieve=_retrieve)


def schema_ref_for(odata_type: str) -> str:
    """Return the unversioned schema ``$ref`` for a Redfish ``@odata.type``.

    Handles versioned (``#ComputerSystem.v1_16_0.ComputerSystem``), collection
    (``#ChassisCollection.ChassisCollection``), and old-format
    (``#TaskService.0.94.0.Task``) types: namespace is the first segment, the
    type is the last, any version in between is ignored.
    """
    parts = odata_type.lstrip("#").split(".")
    if len(parts) < 2 or not parts[0] or not parts[-1]:
        raise ValueError(f"unrecognized @odata.type: {odata_type!r}")
    namespace, type_name = parts[0], parts[-1]
    return f"{PREFIX}{namespace}.json#/definitions/{type_name}"


def _strip_oem(obj) -> None:
    if isinstance(obj, dict):
        obj.pop("Oem", None)
        for value in obj.values():
            _strip_oem(value)
    elif isinstance(obj, list):
        for value in obj:
            _strip_oem(value)


def _reduce_collection_members(obj: dict) -> None:
    """Reduce a collection's ``Members`` to references for validation.

    Redfish collection schemas type ``Members`` as references (``{@odata.id}``).
    Real services (notably Dell iDRAC, and any ``$expand`` response) inline the
    full member objects. We validate the collection's reference structure here;
    each inlined member is validated on its own as its individual resource.
    """
    members = obj.get("Members")
    if isinstance(members, list):
        obj["Members"] = [
            {"@odata.id": m["@odata.id"]}
            if isinstance(m, dict) and "@odata.id" in m else m
            for m in members
        ]


def validate_payload(payload: dict, strip_oem: bool = True) -> list:
    """Validate a Redfish resource. Returns a sorted list of errors ([] = valid).

    Raises ``SchemaUnavailable`` when the resource type has no standard schema
    (e.g. a Dell OEM type), and ``ValueError`` when ``@odata.type`` is missing.
    """
    odata_type = payload.get("@odata.type")
    if not odata_type:
        raise ValueError("payload has no @odata.type")
    body = deepcopy(payload)
    if strip_oem:
        _strip_oem(body)
    _reduce_collection_members(body)
    validator = Draft7Validator({"$ref": schema_ref_for(odata_type)}, registry=_REGISTRY)
    try:
        errors = list(validator.iter_errors(body))
    except Unresolvable as err:
        # a referenced schema (often an OEM type) has no standard definition
        raise SchemaUnavailable(str(err)) from err
    return sorted(errors, key=lambda e: list(e.absolute_path))
