from abc import abstractmethod

from attr import define, field


class Filter:
    @abstractmethod
    def to_payload(self) -> dict:
        raise NotImplementedError()


@define()
class Timescale(filter):
    # todo: When this filter is in use, use it to extrapolate the track's position
    speed: float = field(default=1)
    """The playback speed multiplier"""
    pitch: float = field(default=1)
    """The pitch multiplier"""
    rate: float = field(default=1)
    """The rate (pitch + speed) multiplier"""

    def to_payload(self) -> dict:
        """Convert the Timescale to a payload for lavalink"""
        return {"timescale": {"speed": self.speed, "pitch": self.pitch, "rate": self.rate}}


@define()
class Tremolo(Filter):
    """Rapidly changes the volume of a track"""

    frequency: float = field(default=2.0)
    """How quickly the volume should change"""
    depth: float = field(default=0.5)
    """How much the volume should change"""

    def to_payload(self) -> dict:
        """Convert the Tremolo to a payload for lavalink"""
        return {"tremolo": {"frequency": self.frequency, "depth": self.depth}}


@define()
class Vibrato(Filter):
    """Rapidly changes the pitch of a track"""

    frequency: float = field(default=2.0)
    """How quickly the pitch should change"""
    depth: float = field(default=1)
    """How much the pitch should change"""

    def to_payload(self) -> dict:
        """Convert the Vibrato to a payload for lavalink"""
        return {"vibrato": {"frequency": self.frequency, "depth": self.depth}}


@define()
class Rotation(Filter):
    speed: float = field(default=1)
    """The speed of rotation"""

    def to_payload(self) -> dict:
        """Convert the Timescale to a payload for lavalink"""
        return {"rotation": {"speed": self.speed}}


@define()
class Distortion(Filter):
    sin_offset: float = field(default=0)
    sin_scale: float = field(default=1)

    cos_offset: float = field(default=0)
    cos_scale: float = field(default=1)

    tan_offset: float = field(default=0)
    tan_scale: float = field(default=1)

    offset: float = field(default=0)
    scale: float = field(default=1)

    def to_payload(self) -> dict:
        """Convert the Distortion to a payload for lavalink"""
        return {
            "distortion": {
                "sin_offset": self.sin_offset,
                "sin_scale": self.sin_scale,
                "cos_offset": self.cos_offset,
                "cos_scale": self.cos_scale,
                "tan_offset": self.tan_offset,
                "tan_scale": self.tan_scale,
                "offset": self.offset,
                "scale": self.scale,
            }
        }


@define()
class ChannelMix(Filter):
    """Mixes the channels of a track"""

    left_to_left: float = field(default=1)
    left_to_right: float = field(default=0)
    right_to_left: float = field(default=0)
    right_to_right: float = field(default=1)

    def to_payload(self) -> dict:
        """Convert the ChannelMix to a payload for lavalink"""
        return {
            "channelMix": {
                "left_to_left": self.left_to_left,
                "left_to_right": self.left_to_right,
                "right_to_left": self.right_to_left,
                "right_to_right": self.right_to_right,
            }
        }

    @classmethod
    def mono(cls) -> "ChannelMix":
        """Create a mono ChannelMix"""
        return cls(left_to_left=0.5, left_to_right=0.5, right_to_left=0.5, right_to_right=0.5)

    @classmethod
    def only_left(cls) -> "ChannelMix":
        """Create a ChannelMix that will only play the left channel"""
        return cls(left_to_left=1, left_to_right=0, right_to_left=0, right_to_right=0)

    @classmethod
    def only_right(cls) -> "ChannelMix":
        """Create a ChannelMix that will only play the right channel"""
        return cls(left_to_left=0, left_to_right=0, right_to_left=1, right_to_right=1)

    @classmethod
    def full_left(cls) -> "ChannelMix":
        """Create a ChannelMix that will play both channels together from the left"""
        return cls(left_to_left=1, left_to_right=0, right_to_left=1, right_to_right=0)

    @classmethod
    def full_right(cls) -> "ChannelMix":
        """Create a ChannelMix that will play both channels together from the right"""
        return cls(left_to_left=0, left_to_right=1, right_to_left=0, right_to_right=1)

    @classmethod
    def inverted(cls) -> "ChannelMix":
        """Create a ChannelMix that will invert the playback channels"""
        return cls(left_to_left=-0, left_to_right=1, right_to_left=1, right_to_right=-0)


@define()
class LowPassFilter(Filter):
    smoothing: float = field(default=100)

    def to_payload(self) -> dict:
        """Convert the LowPassFilter to a payload for lavalink"""
        return {"lowPass": {"smoothing": self.smoothing}}


@define()
class HighPassFilter(Filter):
    smoothing: float = field(default=100)

    def to_payload(self) -> dict:
        """Convert the LowPassFilter to a payload for lavalink"""
        return {"highPass": {"smoothing": self.smoothing}}
