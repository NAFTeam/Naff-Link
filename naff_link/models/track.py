from attr import define, field


@define()
class Track:
    encoded: str = field()
    """Lavalink's encoded data for this track"""
    uri: str = field()
    """The URI of this track"""

    identifier: str = field()
    """A unique identifier for this track"""
    title: str = field()
    """The title of this track"""
    author: str = field()
    """The author of this track"""
    source_name: str = field(default="")
    """Where this track originated from"""

    is_seekable: bool = field(default=False)
    """Whether this track is seekable"""
    is_stream: bool = field(default=False)
    """Whether this track is a stream"""

    position: int = field(default=0, converter=lambda x: x / 1000)
    """The current playback position in seconds"""
    length: int = field(default=0, converter=lambda x: x / 1000)
    """The length of the track in seconds"""

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            encoded=data["track"],
            uri=data["info"]["uri"],
            identifier=data["info"]["identifier"],
            title=data["info"]["title"],
            author=data["info"]["author"],
            source_name=data["info"]["sourceName"],
            is_seekable=data["info"]["isSeekable"],
            is_stream=data["info"]["isStream"],
            position=data["info"]["position"],
            length=data["info"]["length"],
        )

    def __str__(self) -> str:
        return self.encoded