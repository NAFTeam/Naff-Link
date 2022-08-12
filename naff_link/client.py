import asyncio

import aiohttp
from naff import Snowflake_Type, to_snowflake, Listener
from naff import Client as NaffClient
from naff.api.events import RawGatewayEvent

from . import get_logger
from .models.voice_state import VoiceState
from .websocket import WebSocket

log = get_logger()


class Client:
    def __init__(self, naff):
        self.session = None

        self.ws: WebSocket = None
        self.naff: NaffClient = naff

        self.session_id = {}

        # hook into naff's event dispatcher
        self.naff.add_listener(Listener.create("raw_voice_server_update")(self._on_voice_server_update))

    async def connect(self, host: str, port: int, password):
        self.session = aiohttp.ClientSession()
        self.ws = WebSocket(self, self.naff, self.naff.ws, host, port, password)
        await self.ws.connect()

    async def _on_voice_server_update(self, event: RawGatewayEvent):
        guild_id = int(event.data["guild_id"])
        await self.ws.voice_server_update(guild_id, self.session_id[guild_id], event.data)

    async def voice_connect(self, channel: Snowflake_Type, guild: Snowflake_Type, *, timeout: int = 5):
        log.info("Attempting to connect voice to %s", channel)

        guild_id = to_snowflake(guild)
        channel_id = to_snowflake(channel)

        def predicate(event):
            return int(event.data["guild_id"]) == guild_id

        await self.naff.ws.voice_state_update(guild_id, channel_id, False, True)

        try:
            voice_state = await self.naff.wait_for("raw_voice_state_update", predicate, timeout=timeout)
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError("Timed out waiting for voice_state_update and voice_server_update") from e
        self.session_id[guild_id] = voice_state.data["session_id"]

        state = VoiceState.from_dict(voice_state.data, self.naff, self)
        # replace the naff-client's voice state with our own
        self.naff.cache.place_bot_voice_state(state)
        return state

    async def play(self, guild_id: Snowflake_Type, track):
        """
        Play a track.

        Args:
            guild_id: The guild id to play the track in
            track: The track to play
        """
        await self.ws.play(to_snowflake(guild_id), str(track))

    async def stop(self, guild_id: Snowflake_Type):
        """
        Stop playing a track.

        Args:
            guild_id: The guild id to stop playing the track in
        """
        await self.ws.stop(to_snowflake(guild_id))

    async def pause(self, guild_id: Snowflake_Type):
        """
        Pause a track.

        Args:
            guild_id: The guild id to pause the track in
        """
        await self.ws.pause(to_snowflake(guild_id))

    async def resume(self, guild_id: Snowflake_Type):
        """
        Resume a track.

        Args:
            guild_id: The guild id to resume the track in
        """
        await self.ws.pause(to_snowflake(guild_id), False)

    async def seek(self, guild_id: Snowflake_Type, position: float):
        """
        Seek to a position in the track.

        Args:
            guild_id: The guild id to seek in
            position: The position to seek to (in seconds)
        """
        await self.ws.seek(to_snowflake(guild_id), int(position * 1000))

    async def volume(self, guild_id: Snowflake_Type, volume: float) -> float:
        """
        Set the volume of a track.

        Args:
            guild_id: The guild id to set the volume in
            volume: The volume to set (0-1000)
        """
        volume = min(max(0, volume), 1000)
        await self.ws.volume(to_snowflake(guild_id), volume)
        return volume

    async def resolve_track(self, track: str):
        headers = {"Authorization": self.ws.password}
        async with self.session.get(
            f"http://{self.ws.host}:{self.ws.port}/loadtracks?identifier={track}",
            headers=headers,
        ) as resp:
            data = await resp.json()
        return data["tracks"]

    async def decode_track(self, track: str):
        headers = {"Authorization": self.ws.password}
        async with self.session.get(
            f"http://{self.ws.host}:{self.ws.port}/decodetrack?track={track}",
            headers=headers,
        ) as resp:
            data = await resp.json()
        return data
