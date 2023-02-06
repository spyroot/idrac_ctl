class InvalidArgument(Exception):
    pass


class UncommittedPendingChanges(Exception):
    """Must raise if state has Uncommitted changes.
    """
    pass


class InvalidJsonSpec(Exception):
    """Must raise in case json spec is invalid.
    """
    pass


class MissingMandatoryArguments(Exception):
    """Must raise in case argument missing.
    """
    pass


class FailedDiscoverAction(Exception):
    """Must raise if requested action failed to discover.
    i.e. old IDRAC version for example.
    """
    pass


class NoPendingValues(Exception):
    """Must raise if failed discover action.
    """
    pass


class UnsupportedAction(Exception):
    pass


class PostRequestFailed(Exception):
    pass


class AuthenticationFailed(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class MissingResource(Exception):
    pass


class UnexpectedResponse(Exception):
    pass


class PatchRequestFailed(Exception):
    pass


class DeleteRequestFailed(Exception):
    pass
