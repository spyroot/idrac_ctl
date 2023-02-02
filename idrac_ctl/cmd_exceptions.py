class InvalidArgument(Exception):
    pass


class FailedDiscoverAction(Exception):
    """Must raise if failed discover action.
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

