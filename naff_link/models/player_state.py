from attr import define, field


@define()
class PlayerState:
    connected: bool = field(default=False)
    """Whether the player is connected to a voice channel."""
    position: float = field(default=0, converter=lambda x: x / 1000)
    """The position of the player in seconds."""
    time: int = field(default=0)
    """The time this state was received (unix timestamp)."""
