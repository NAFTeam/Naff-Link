class LinkException(Exception):
    ...


class LinkConnectionError(LinkException):
    ...


class PlayerError(LinkException):
    ...


class StreamException(LinkException):
    ...


class NotPlayingException(PlayerError):
    ...
