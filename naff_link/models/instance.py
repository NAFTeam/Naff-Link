from typing import TYPE_CHECKING

from attr import define, field
from naff import MISSING

from naff_link import get_logger
from naff_link.models.stats import Stats
from naff_link.rest_api import RESTClient
from naff_link.websocket import WebSocket

if TYPE_CHECKING:
    from naff_link.client import Client

log = get_logger()


@define()
class Instance:
    _link_client: "Client" = field()

    host: str = field()
    port: int = field()
    password: str = field()

    stats: Stats = field(default=MISSING)

    region: str = field(default=None)
    _name_override: str = field(default=None)
    _guild_ids: set[int] = field(factory=set)

    _ws: WebSocket = field(default=MISSING)
    _rest: RESTClient = field(default=MISSING)

    @classmethod
    def create(cls, client, host, port, password, *, region=None, name_override=None):
        instance = cls(client, host, port, password)
        instance.region = region
        instance._name_override = name_override
        return instance

    @property
    def name(self) -> str:
        return self._name_override or f"{f'{self.region}::' if self.region else ''}{self.host}::{self.port}"

    @property
    def is_connected(self) -> bool:
        if self._ws:
            return self._ws.is_connected
        return False

    @property
    def guild_ids(self):
        return self._guild_ids

    @property
    def ws(self):
        return self._ws

    @property
    def load_penalty(self) -> float:
        """Calculate the load penalty for this instance."""
        # derived from https://github.com/freyacodes/Lavalink-Client/blob/master/src/main/java/lavalink/client/io/LavalinkLoadBalancer.java        playing_players = self.stats.playing_players
        if not self.stats:
            return float("inf")
        playing_players = self.stats.playing_players
        try:
            cpu_penalty = 1.05 ** (100 * self.stats.system_load) * 10 - 10
        except TypeError:
            breakpoint()
        null_frame_penalty = 0
        deficit_frames_penalty = 0

        if self.stats.null_frames:
            null_frame_penalty = (1.03 ** (500 * (self.stats.null_frames / 3000))) * 300 - 300
            null_frame_penalty *= 2

        if self.stats.deficit_frames:
            deficit_frames_penalty = (1.03 ** (500 * (self.stats.deficit_frames / 3000))) * 600 - 600

        total = playing_players + cpu_penalty + null_frame_penalty + deficit_frames_penalty
        return total

    async def connect(self) -> None:
        if not self._link_client.session:
            raise RuntimeError("No session available to connect to lavalink")

        self._ws = WebSocket(self._link_client, self._link_client.naff, self._link_client.naff.ws, self)
        self._rest = RESTClient(self._link_client, self)
        await self._ws.connect()

        log.info(f"Connected to Lavalink instance: {self.name}")

    def update_stats(self, data: dict):
        self.stats = Stats.from_dict(data)
        log.debug(f"Updated stats for {self.name} :: {self.load_penalty = }")
