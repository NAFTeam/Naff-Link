from typing import Optional, TYPE_CHECKING

from attr import define, field
from naff import MISSING, to_snowflake, Timestamp
from naff import VoiceState as NAFFVoiceState
from naff import Client as NAFFClient
from naff.client.utils import optional


if TYPE_CHECKING:
    from naff_link.client import Client as NaffLinkClient


@define()
class VoiceState(NAFFVoiceState):
    naff_link: "NaffLinkClient" = field()

    current_track: dict = field(default=None)

    _volume: float = field(default=100)
    _playing: bool = field(default=False)
    _paused: bool = field(default=False)

    # standard voice states expect this data, this voice state lacks it initially; so we make them optional
    user_id: "Snowflake_Type" = field(default=MISSING, converter=optional(to_snowflake))
    _guild_id: Optional["Snowflake_Type"] = field(default=None, converter=optional(to_snowflake))
    _member_id: Optional["Snowflake_Type"] = field(default=None, converter=optional(to_snowflake))

    def __attrs_post_init__(self) -> None:
        # jank line to handle the two inherently incompatible data structures
        self._member_id = self.user_id = self._client.user.id

    async def _voice_server_update(self, *args) -> None:
        return

    async def _voice_state_update(self, *args) -> None:
        return

    @classmethod
    def from_dict(cls, data: dict, naff_client: NAFFClient, naff_link: "NaffLinkClient"):
        data = cls._process_dict(data, naff_client)
        return cls(**data, naff_link=naff_link, client=naff_client)

    @property
    def volume(self) -> float:
        """Get the volume of the player"""
        return self._volume

    @property
    def paused(self) -> bool:
        """Is the player currently paused"""
        return self._paused

    @property
    def playing(self) -> bool:
        """Is the player currently playing"""
        return self._playing

    async def set_volume(self, volume: float) -> float:
        """Set the volume of the player"""
        set_volume = await self.naff_link.volume(self.guild.id, volume)
        self._volume = set_volume
        return set_volume

    async def play(self, track: str) -> dict:
        """Play a track"""
        return await self.naff_link.play(self.guild.id, track)