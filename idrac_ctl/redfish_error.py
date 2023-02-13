"""Redfish implementation based
https://www.dmtf.org/standards/REDFISH

A mapping redfish error python object.

Author Mus spyroot@gmail.com
"""
from typing import Optional, List


class RedfishErrorMessage:
    def __init__(self,
                 message_id: Optional[str] = "",
                 message: Optional[str] = "",
                 related: List[str] = None,
                 message_args: Optional[str] = None,
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
        self.message_args = message_args


class RedfishError:
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
        self._code = code
        self._message = message
        if message_extended is None:
            self._message_extended = []
        else:
            self._message_extended = message_extended

        self._status_code = http_status_code
        self._exception_msg = exception_msg

    @property
    def code(self) -> str:
        """code from error message from redfish error"""
        return self._code

    @property
    def message(self) -> str:
        """Message from redfish error.
        :return:
        """
        return self._message

    @property
    def status_code(self) -> int:
        """http status code that issue error.
        :return:
        """
        return self._status_code

    @property
    def message_extended(self) -> list[RedfishErrorMessage]:
        """return a list of error message based on spec
        :return:  RedfishErrorMessage
        """
        return self._message_extended

    @message.setter
    def message(self, value) -> None:
        self._message = value

    @message_extended.setter
    def message_extended(self, value) -> None:
        """a value must a list.
        :param value:
        :return: None
        """
        if not isinstance(value, list):
            return

        for v in value:
            err_msg = RedfishErrorMessage()

            if hasattr(v, "MessageId"):
                err_msg.message_id = v.MessageId
            if hasattr(v, "Message"):
                err_msg.message = v.Message
            if hasattr(v, "MessageArgs"):
                err_msg.message_args = v.MessageArgs
            if hasattr(v, "MessageSeverity"):
                err_msg.message_severity = v.MessageSeverity
            if hasattr(v, "Severity"):
                err_msg.severity = v.Severity
            if hasattr(v, "Resolution"):
                err_msg.resolution = v.Resolution

            self._message_extended.append(err_msg)
