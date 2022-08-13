import struct
import time
from base64 import b64decode
from io import BytesIO

from attr import define, field

from naff_link import get_logger

log = get_logger()


@define()
class Track:
    encoded: str = field()
    """Lavalink's encoded data for this track"""
    uri: str = field()
    """The URI of this track"""

    identifier: str = field()
    """A unique identifier for this track"""
    title: str = field(repr=True)
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
    timestamp: int = field(factory=lambda: time.time())
    """The timestamp of when this track was last updated"""

    @classmethod
    def from_dict(cls, data: dict):
        if "info" in data:
            data |= {k: v for k, v in data["info"].items()}

        try:
            return cls(
                encoded=data["track"],
                uri=data["uri"],
                identifier=data["identifier"],
                title=data["title"],
                author=data["author"],
                source_name=data["sourceName"],
                is_seekable=data["isSeekable"],
                is_stream=data["isStream"],
                position=data["position"],
                length=data["length"],
            )
        except KeyError as e:
            log.error(f"Missing key in track data: {e} :: {data}")

    @classmethod
    def from_encode(cls, encoded: str) -> "Track":
        data = BytesIO(b64decode(encoded))

        flags = (struct.unpack(">i", data.read(4))[0] & 0xC0000000) >> 30
        # version data we dont care about
        _ = struct.unpack("B", data.read(1)) if flags & 1 != 0 else 1

        title_length = struct.unpack(">H", data.read(2))[0]
        title = data.read(title_length).decode(errors="ignore")

        author_length = struct.unpack(">H", data.read(2))[0]
        author = data.read(author_length).decode(errors="ignore")

        track_length = struct.unpack(">Q", data.read(8))[0]

        identifier_length = struct.unpack(">H", data.read(2))[0]
        identifier = data.read(identifier_length).decode(errors="ignore")

        is_stream = bool(struct.unpack("B", data.read(1))[0])

        if bool(struct.unpack("B", data.read(1))[0]):
            uri_length = struct.unpack(">H", data.read(2))[0]
            uri = data.read(uri_length).decode(errors="ignore")

        source_length = struct.unpack(">H", data.read(2))[0]
        source = data.read(source_length).decode(errors="ignore")
        position = struct.unpack(">Q", data.read(8))[0]

        return cls(
            encoded=encoded,
            uri=uri,
            identifier=identifier,
            title=title,
            author=author,
            source_name=source,
            is_seekable=not is_stream,
            is_stream=is_stream,
            position=position,
            length=track_length,
        )

    def __str__(self) -> str:
        return self.encoded

    def __repr__(self) -> str:
        if self.author:
            return f"<Track {self.title} by {self.author}>"
        return f"<Track {self.title}>"
