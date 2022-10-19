from typing import TYPE_CHECKING

from attr import define, field
from naff import to_snowflake
from naff.api.events import BaseEvent

from naff_link.models.player_state import PlayerState
from naff_link.models.stats import Stats
from naff_link.models.track import Track

if TYPE_CHECKING:
    from naff_link.client import Client
    from naff_link.models.instance import Instance


@define()
class _BaseLavaEvent(BaseEvent):
    naff_link: "Client" = field()

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        raise NotImplementedError()


@define()
class PlayerUpdate(_BaseLavaEvent):
    state: PlayerState = field()
    guild_id: int = field(converter=to_snowflake)

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        return cls(
            state=PlayerState(**data["state"]),
            guild_id=data["guildId"],
            naff_link=naff_link,
        )


@define()
class TrackStart(_BaseLavaEvent):
    _track_encode: str = field()
    guild_id: int = field()

    @property
    def track(self):
        return Track.from_encode(self._track_encode)

    async def fetch_track(self):
        data = await self.naff_link.decode_track(self._track_encode)
        return data

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        return cls(
            track_encode=data["track"],
            guild_id=data["guildId"],
            naff_link=naff_link,
        )


@define()
class TrackEnd(TrackStart):
    reason: str = field()

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        return cls(
            track_encode=data["track"],
            guild_id=data["guildId"],
            reason=data["reason"],
            naff_link=naff_link,
        )


@define()
class TrackException(_BaseLavaEvent):
    ...

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        ...


@define()
class TrackStuck(TrackStart):
    threshold: float = field(converter=lambda x: x / 1000)
    """The threshold in seconds"""

    @classmethod
    def from_dict(cls, naff_link: "Client", data: dict):
        return cls(
            track_encode=data["track"],
            guild_id=data["guildId"],
            threshold=data["thresholdMs"],
            naff_link=naff_link,
        )


@define()
class StatsUpdate(_BaseLavaEvent):
    stats: Stats = field()
    instance: "Instance" = field()

    @classmethod
    def from_dict(cls, naff_link: "Client", instance: "Instance", data: dict):
        return cls(stats=Stats.from_dict(data), naff_link=naff_link, instance=instance)


# aforementioned blackjack and hookers
