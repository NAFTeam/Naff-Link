from typing import Optional, TYPE_CHECKING

from attr import define, field
from naff import Client as NAFFClient
from naff import MISSING, to_snowflake
from naff import VoiceState as NAFFVoiceState
from naff.client.utils import optional

from naff_link.errors import StreamException, NotPlayingException
from naff_link.events import PlayerUpdate
from naff_link.models.equalizer import Equalizer
from naff_link.models.track import Track

if TYPE_CHECKING:
    from naff_link.client import Client as NaffLinkClient


@define()
class VoiceState(NAFFVoiceState):
    naff_link: "NaffLinkClient" = field()

    current_track: Track = field(default=None)

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

    async def _voice_state_update(self, _, __, data) -> None:
        self.update_from_dict(data)

    async def player_state_update(self, event: PlayerUpdate):
        if self.current_track:
            self.current_track.position = event.state.position

    async def track_update(self, track: Track) -> None:
        """Update the current track"""
        self.current_track = track

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

    async def set_equalizer(self, eq: Equalizer) -> None:
        """
        Set the equalizer of the player

        Args:
            eq: The equalizer to set
        """
        return await self.naff_link.set_equalizer(self.guild.id, eq)

    async def seek(self, position: float) -> float:
        """
        Seek to a position in the track

        Args:
            position: The position to seek to (in seconds)

        Raises:
            NotPlayingException: If the player is not playing
            StreamException: If the player is playing a stream
        """
        if self.current_track:
            if not self.current_track.is_stream:
                return await self.naff_link.seek(self.guild.id, position)
            raise StreamException("Cannot seek in streams")
        raise NotPlayingException("Cannot seek when not playing")

    async def pause(self) -> None:
        """Pause the player"""
        if self._paused:
            await self.naff_link.resume(self.guild.id)
        else:
            await self.naff_link.pause(self.guild.id)
        self._paused = not self._paused

    async def resume(self) -> None:
        """Resume the player"""
        await self.naff_link.resume(self.guild.id)
        self._paused = False

    async def play(self, track: str) -> dict:
        """Play a track"""
        return await self.naff_link.play(self.guild.id, track)
