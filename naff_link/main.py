import asyncio
import logging
import re
from typing import TYPE_CHECKING

from lavalink import (
    Client as LavalinkClient,
    DefaultPlayer,
    BasePlayer,
    NodeConnectedEvent,
    Source,
    Node,
    LoadResult,
)
from naff import Extension, MISSING, listen, to_snowflake

from naff_link.events import NaffLinkEvent

if TYPE_CHECKING:
    from naff import Snowflake_Type

_event_reg = re.compile("(?<!^)(?=[A-Z])")

log = logging.getLogger("NAFF-Link")


class NaffLink(Extension):
    def __init__(self, bot):
        super().__init__()
        self.lavalink: LavalinkClient = MISSING
        self.ready: asyncio.Event = asyncio.Event()

        if hasattr(bot, "lavalink"):
            log.warning("NaffLink is already loaded. You should only load it once.")

        self.bot.naff_link = self

    async def async_start(self):
        self.lavalink = LavalinkClient(self.bot.app.id, player=DefaultPlayer)
        self.lavalink.add_event_hook(self.on_lavalink_event)
        log.info("NAFFLink has successfully hooked into Lavalink.")

    @listen()
    async def __on_raw_voice_state_update(self, event):
        await self.lavalink.voice_update_handler(
            {"t": "VOICE_STATE_UPDATE", "d": event.data}
        )

    @listen()
    async def __on_raw_voice_server_update(self, event):
        await self.lavalink.voice_update_handler(
            {"t": "VOICE_SERVER_UPDATE", "d": event.data}
        )

    async def on_lavalink_event(self, event):
        """
        Patches lavalink events to be compatible with naff and dispatches them.

        Args:
            event: The link_event to dispatch.
        """
        naff_event = NaffLinkEvent(
            link_event=event, override_name=event.__class__.__name__
        )
        self.bot.dispatch(naff_event)

    @listen()
    async def on_node_connected_event(self, event):
        link_event: NodeConnectedEvent = event.link_event
        log.info(f"Connected to lavalink node {link_event.node.name}")
        self.ready.set()

    async def connect_to_vc(
        self,
        guild: "Snowflake_Type",
        channel: "Snowflake_Type",
        muted: bool = False,
        deafened: bool = True,
    ) -> DefaultPlayer:
        guild_id = to_snowflake(guild)
        channel_id = to_snowflake(channel)
        ws = self.bot.get_guild_websocket(guild_id)

        player = self.lavalink.player_manager.create(guild_id)
        await ws.voice_state_update(guild_id, channel_id, muted, deafened)

        return player

    async def disconnect(self, guild: "Snowflake_Type", *, force: bool = False) -> None:
        """
        Disconnects the bot from the voice channel it is in.

        Args:
            guild: The guild to disconnect from.
        """
        guild_id = to_snowflake(guild)
        player = self.get_player(guild_id)
        ws = self.bot.get_guild_websocket(guild_id)

        if not force and not player.is_connected:
            return

        await ws.voice_state_update(guild_id, None)
        await player.stop()
        player.channel_id = None

    def get_player(self, guild: "Snowflake_Type") -> DefaultPlayer:
        guild_id = to_snowflake(guild)
        return self.lavalink.player_manager.players.get(guild_id)

    def add_node(
        self,
        host: str,
        port: int,
        password: str,
        region: str,
        resume_key: str = None,
        resume_timeout: int = 60,
        name: str = None,
        reconnect_attempts: int = 3,
        filters: bool = True,
        ssl: bool = False,
    ):
        self.lavalink.add_node(
            host=host,
            port=port,
            password=password,
            region=region,
            resume_key=resume_key,
            resume_timeout=resume_timeout,
            name=name,
            reconnect_attempts=reconnect_attempts,
            filters=filters,
            ssl=ssl,
        )

    def register_source(self, source: Source) -> None:
        """
        Registers a source that lavalink can use to get tracks.

        Args:
            source: The source to register
        """
        return self.lavalink.register_source(source)

    async def get_tracks(
        self, query: str, node: Node = None, check_local: bool = False
    ) -> LoadResult:
        """
        Retrieves a list of tracks pertaining to the provided query.

        Args:
            query: The query to perform a search for.
            node: The node to use for track lookup. Leave this blank to use a random node.
            check_local: Whether to also search the query on sources registered with this Lavalink client.
        """
        return await self.lavalink.get_tracks(query, node=node, check_local=check_local)
