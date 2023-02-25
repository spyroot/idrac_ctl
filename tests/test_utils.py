import json
from typing import Optional

from requests.models import Response


def create_json_resp(
        data, status_code: Optional[int] = 200,
        headers=None,
        encoding: Optional[str] = "utf8"):
    """Create json respond object for unit testing.

    :param data: a data
    :param encoding:  default json encoding
    :param status_code:  a synthetically generated status code
    :param headers:  synthetically generated http headers
    :return:
    """
    if headers is None:
        headers = {}

    resp = Response()
    resp._content = json.dumps(data).encode("utf8")
    resp.status_code = status_code
    resp._headers = headers
    resp._content_type = "application/json"
    return resp
