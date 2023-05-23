"""Redfish implementation based
https://www.dmtf.org/standards/REDFISH

A mapping redfish error python object.

Author Mus spyroot@gmail.com
"""
from typing import Optional, List
from .redfish_shared import RedfishJsonMessage as jsonMessage


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

        :param message_id:  message id
        :param message: Human-readable error message that indicates the semantics associated with the error
        :param related: Substitution parameter values for the message.
        If the parameterized message defines a MessageId , the service shall include the MessageArgs in the response.
        :param message_args: Substitution parameter values for the message.
                            If the parameterized message defines a MessageId ,
                            the service shall include the MessageArgs in the response.
        :param message_severity: Severity of the error.
        :param severity: Severity of the error
        :param resolution: recommended actions to take to resolve the error
        """
        if not isinstance(message_args, list):
            raise TypeError("message_args must be a list")
        if not isinstance(related, list):
            raise TypeError("related must be a list")

        if message_args is None:
            message_args = []

        if related is None:
            related = []

        self.message = message
        self.related = related
        self.message_id = message_id
        self.resolution = resolution

        # deprecated
        self.severity = severity
        self.message_severity = message_severity

        if message_args is None:
            self.message_args = []
        else:
            self.message_args = message_args

        self.message_count = 0
        self.related_count = 0
        self.message_args_count = 0


class RedfishRespondMessage:
    def __init__(self,
                 http_status_code: int,
                 code: Optional[str] = "",
                 message: Optional[str] = "root",
                 message_extended: List[RedfishMessage] = None,
                 exception_msg: Optional[str] = ""):
        """
        Redfish specs defines a verbose output.  THis generic respond msg.

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

        if not isinstance(self._message_extended, list):
            self._message_extended = []

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
    def message_extended(self) -> list[RedfishMessage]:
        """return a list it encapsulates Message.ExtendedInfo based
        on redfish spec
        :return:  RedfishErrorMessage
        """
        return self._message_extended

    @message.setter
    def message(self, value: str) -> None:
        self._message = value

    @staticmethod
    def new_msg():
        """
        :return:
        """
        return RedfishMessage()

    @staticmethod
    def is_redfish_msg(obj):
        """
        :param obj:
        :return:
        """
        return obj is not None and isinstance(obj, dict) \
            and jsonMessage.MessageExtendedInfo in obj

    @staticmethod
    def redfish_odata_count_map(json_dict: dict) -> dict[str]:
        """Return a dict that store for each list property it
           respected  @odata.counts property
        :param json_dict:
        :return:
        """
        odata_counts_keys = {}
        for k in json_dict.keys():
            # for each key that value is list we expect data count
            if isinstance(json_dict[k], list):
                odata_count = f"{json_dict[k]}@odata.count"
                if odata_count in json_dict:
                    odata_counts_keys[k] = odata_count

        return odata_counts_keys

    @message_extended.setter
    def message_extended(self, value) -> None:
        """a value must a list.
        :param value:
        :return: None
        """

        if isinstance(value, dict) and jsonMessage.MessageExtendedInfo in value:
            json_list = value[jsonMessage.MessageExtendedInfo]
        elif isinstance(value, list):
            json_list = value
        else:
            return

        for v in json_list:
            if not isinstance(v, dict):
                continue
            # data_count_map = self.redfish_odata_count_map(v)

            # msg.add_property(data_count_map)
            msg = RedfishMessage()
            msg.message_id = v.get(jsonMessage.MessageId, "")
            msg.message = v.get(jsonMessage.Message, "")

            if jsonMessage.MessageId.lower() in v:
                msg.message = v[jsonMessage.Message.lower()]

            message_args = v.get(jsonMessage.MessageArgs, [])
            if isinstance(message_args, list):
                msg.message_args = message_args
            else:
                msg.message_args.append(message_args)

            msg.message_severity = v.get(jsonMessage.MessageSeverity, v.get(jsonMessage.Severity, ""))
            msg.message_severity = v.get(jsonMessage.MessageSeverity, v.get(jsonMessage.Severity, ""))
            msg.resolution = v.get(jsonMessage.Resolution, v.get(jsonMessage.Resolution.lower(), ""))
            msg.message_count = int(v.get(jsonMessage.MessageArgsCount, 0))
            msg.related_count = int(v.get(jsonMessage.RelatedPropertiesCount, 0))
            msg.severity = v.get(jsonMessage.Severity, "")

            self._message_extended.append(msg)

    def __repr__(self) -> str:
        """
        :return:
        """
        msgs = [m.message for m in self._message_extended]
        return "\n".join(msgs) + "\n"
