"""Redfish implementation based
https://www.dmtf.org/standards/REDFISH

A mapping redfish error python object.

Author Mus spyroot@gmail.com
"""
from typing import Optional, List

from idrac_ctl.redfish_respond import RedfishRespondMessage


class RedfishMessage:
    """Generic redfish error"""

    def __init__(self,
                 message_id: Optional[str] = "",
                 message: Optional[str] = "",
                 related: Optional[List[str]] = None,
                 message_args: Optional[List[str]] = None,
                 message_severity: Optional[str] = "",
                 severity: Optional[str] = "",
                 resolution: Optional[str] = ""
                 ):
        """
        Each instance of a message object shall contain at least a MessageId ,
        together with any applicable MessageArgs , or a Message property that defines
        the complete human-readable error message.

        :param message_id: Error or message.
        :param message: Human-readable error message that indicates the semantics associated with the error
        :param related: Substitution parameter values for the message.
        If the parameterized message defines a MessageId , the service shall include the MessageArgs in the response.
        :param message_args: Substitution parameter values for the message.
                            If the parameterized message defines a MessageId ,
                            the service shall include the MessageArgs in the response.
        :param message_severity: Severity of the error.
        :param severity: Severity of the error
        :param resolution: Recommended actions to take to resolve the error
        """
        if message_args is None:
            message_args = []

        self.message_id = message_id
        self.message = message
        self.related = related
        self.resolution = resolution
        # deprecated
        self.severity = severity
        self.message_severity = message_severity

        if message_args is None:
            self.message_args = []
        else:
            self.message_args = message_args

        self.message_count = 0


class RedfishErrorMessage(RedfishMessage):
    def __init__(self,
                 message_id: Optional[str] = "",
                 message: Optional[str] = "",
                 related: Optional[List[str]] = None,
                 message_args: Optional[List[str]] = None,
                 message_severity: Optional[str] = "",
                 severity: Optional[str] = "",
                 resolution: Optional[str] = ""
                 ):
        """
        :param message_id: str: error msg id
        :param message:
        :param related:
        :param message_args:
        :param message_severity:
        :param severity:
        :param resolution:
        """
        super().__init__(
            message_id=message_id,
            message=message,
            related=related,
            message_args=message_args,
            message_severity=message_severity,
            severity=severity,
            resolution=resolution
        )


class RedfishError(RedfishRespondMessage):
    """
    Redfish error.  Please check for DSP0266. In high level it just more verbose
    chatty error respond.  How useful is that I'm not 100 sure :-)

    Note on top of describe properties, object store original http code server responded.
    So caller can make a decision what to do, also store _exception_msg in case
    JSON Decoder failed to decode error. ( this mainly if server responded with some dodgy
    replay)
    """

    def __init__(self,
                 http_status_code: int,
                 code: Optional[str] = "",
                 message: Optional[str] = "root",
                 message_extended: List[RedfishErrorMessage] = None,
                 exception_msg: Optional[str] = ""):
        """
        Redfish specs defines a verbose output. Motivation that is has more information
        about the error as possible.  It also defines multiply errors.
        :param code: a string
        :param message: Displays a human-readable error message that corresponds
                        to the message in the message registry.
        :param message_extended: list of redfish that describe one or more error messages.
        """
        super().__init__(
            http_status_code=http_status_code,
            code=code, message=message,
            message_extended=message_extended,
        )
        super().__init__(http_status_code=http_status_code,
                         code=code, message=message,
                         message_extended=message_extended)

    @staticmethod
    def new_msg():
        return RedfishErrorMessage()

    @property
    def message_extended(self) -> list[RedfishMessage]:
        """return a list of error message based on spec
        :return:  RedfishErrorMessage
        """
        return self._message_extended

    def __repr__(self) -> str:
        msgs = [m.message for m in self._message_extended]
        return "\n".join(msgs) + "\n"

    @message_extended.setter
    def message_extended(self, value):
        self._message_extended = value
