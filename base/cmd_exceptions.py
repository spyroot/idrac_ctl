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
