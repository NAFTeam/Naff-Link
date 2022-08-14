import asyncio

import aiohttp
from naff import Client as NaffClient
from naff import Snowflake_Type, to_snowflake, Listener
from naff.api.events import RawGatewayEvent

from . import get_logger
from .events import PlayerUpdate, TrackStart, TrackEnd
from .models.equalizer import Equalizer
from .models.filters import Filter
from .models.track import Track
from .models.voice_state import VoiceState
from .rest_api import RESTClient
from .websocket import WebSocket

log = get_logger()


class Client:
    def __init__(self, naff, hostname: str, port: int, password: str):
        self.session = None

        self.ws: WebSocket = None
        self.rest: RESTClient = None
        self.naff: NaffClient = naff

        self.session_ids = {}

        self.host: str = hostname
        self.port: int = port
        self.password: str = password

        # hook into naff's event dispatcher
        self.naff.add_listener(Listener.create("raw_voice_server_update")(self._on_voice_server_update))
        self.naff.add_listener(Listener.create("player_update")(self._player_state_update))
        self.naff.add_listener(Listener.create("track_start")(self._track_update))
        self.naff.add_listener(Listener.create("track_end")(self._track_update))

    @classmethod
    async def connect_to(cls, naff_client: NaffClient, host: str, port: int, password: str, *, timeout: int = 5):
        """
        Connect to Lavalink.

        Args:
            naff_client: The naff client your bot is using
            host: The host to connect to
            port: The port to connect to
            password: The password to connect with
            timeout: The timeout to wait for the connection to complete (in seconds)
        """
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
        instance = cls(naff_client, host, port, password)

        instance.session = session
        instance.rest = RESTClient(instance)
        instance.ws = WebSocket(instance, naff_client, naff_client.ws)

        await instance.ws.connect()

        return instance

    async def _on_voice_server_update(self, event: RawGatewayEvent):
        guild_id = int(event.data["guild_id"])
        await self.ws.voice_server_update(guild_id, self.session_ids[guild_id], event.data)

    async def _player_state_update(self, event: PlayerUpdate):
        """Called when a player state update is received. Updates active voice states with data provided."""
        voice_state = self.naff.cache.get_bot_voice_state(event.guild_id)
        if voice_state:
            await voice_state.player_state_update(event)

    async def _track_update(self, event: TrackStart):
        """Called when a track starts playing. Updates active voice states with the track data."""
        voice_state = self.naff.cache.get_bot_voice_state(event.guild_id)
        if voice_state:
            if isinstance(event, TrackEnd):
                log.info(
                    f"{event.guild_id}::Stopped {'streaming' if event.track.is_stream else 'playing'} {event.track.title}"
                )
                await voice_state.track_update(event.track)
            else:
                log.info(
                    f"{event.guild_id}::Started {'streaming' if event.track.is_stream else 'playing'}  {event.track.title}"
                )
                await voice_state.track_update(None)

    async def voice_connect(self, channel: Snowflake_Type, guild: Snowflake_Type, *, timeout: int = 5):
        guild_id = to_snowflake(guild)
        channel_id = to_snowflake(channel)

        log.debug(f"Attempting to connect voice to {guild_id}::{channel_id}")

        def predicate(event):
            return int(event.data["guild_id"]) == guild_id

        await self.naff.ws.voice_state_update(guild_id, channel_id, False, True)

        try:
            voice_state = await self.naff.wait_for("raw_voice_state_update", predicate, timeout=timeout)
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError("Timed out waiting for voice_state_update and voice_server_update") from e
        self.session_ids[guild_id] = voice_state.data["session_id"]

        state = VoiceState.from_dict(voice_state.data, self.naff, self)
        # replace the naff-client's voice state with our own
        self.naff.cache.place_bot_voice_state(state)
        log.info(f"Successfully connected voice to {guild_id}::{channel_id}")
        return state

    async def play(
        self,
        guild_id: Snowflake_Type,
        track,
        *,
        start_time: float = 0,
        end_time: int = None,
        volume: int = None,
        paused: bool = False,
    ):
        """
        Play a track.

        Args:
            guild_id: The guild id to play the track in
            track: The track to play
            start_time: The time to start playing the track at
            end_time: The time to stop playing the track at
            volume: The volume to play the track at
            paused: Whether to start the track paused
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Track Requested: {track}")

        # if track is a url, resolve it first
        if isinstance(track, str) and track.startswith("http"):
            track = await self.resolve_track(track)

        if start_time:
            start_time *= 1000
        if end_time:
            end_time *= 1000

        await self.ws.play(guild_id, str(track), start_time=start_time, end_time=end_time, volume=volume, pause=paused)

    async def stop(self, guild_id: Snowflake_Type):
        """
        Stop playing a track.

        Args:
            guild_id: The guild id to stop playing the track in
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Stopping playback")
        await self.ws.stop(guild_id)

    async def pause(self, guild_id: Snowflake_Type):
        """
        Pause a track.

        Args:
            guild_id: The guild id to pause the track in
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Pausing playback")
        await self.ws.pause(guild_id)

    async def resume(self, guild_id: Snowflake_Type):
        """
        Resume a track.

        Args:
            guild_id: The guild id to resume the track in
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Resuming playback")
        await self.ws.pause(guild_id, False)

    async def seek(self, guild_id: Snowflake_Type, position: float):
        """
        Seek to a position in the track.

        Args:
            guild_id: The guild id to seek in
            position: The position to seek to (in seconds)
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Seeking to {position}")
        await self.ws.seek(guild_id, int(position * 1000))

    async def volume(self, guild_id: Snowflake_Type, volume: float) -> float:
        """
        Set the volume of a track.

        Args:
            guild_id: The guild id to set the volume in
            volume: The volume to set (0-1000)
        """
        volume = min(max(0, volume), 1000)
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Setting volume to {volume}")

        await self.ws.volume(to_snowflake(guild_id), volume)
        return volume

    async def search(self, query, *, engine: str = "ytsearch") -> list[Track]:
        """
        Search for a track.

        Args:
            query: The query to search for
            engine: The engine to search with (default ytsearch)

        Returns:
            A list of tracks that match then given query
        """
        data = await self.rest.resolve_track(f"{engine}: {query}")
        return [Track.from_dict(track) for track in data["tracks"]]

    async def resolve_track(self, track: str) -> Track:
        """
        Resolve a track into a format that can be played.

        Args:
            track: The track to resolve

        Returns:
            The resolved track
        """
        data = await self.rest.resolve_track(track)
        return Track.from_dict(data["tracks"][0])

    async def decode_track(self, track: str) -> Track:
        """
        Decode lavalink's encoded track name into a track object.

        Args:
            track: The track string to decode

        Returns:
            The decoded track
        """
        data = await self.rest.decode_track(track)
        return Track.from_dict(data | {"track": track})

    async def set_equalizer(self, guild_id: Snowflake_Type, eq: Equalizer) -> None:
        """
        Set the equalizer for a guild.

        Args:
            guild_id: The guild id to set the equalizer in
            eq: The eq to set
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Setting equalizer to {eq}")

        payload = eq.to_payload()
        await self.ws.set_equalizer(guild_id, payload)

    async def set_filters(self, guild_id: Snowflake_Type, *filters: Filter | dict) -> None:
        """
        Set the filters for a guild.

        Args:
            guild_id: The guild id to set the filters in
            *filters: The filters to set
        """
        guild_id = to_snowflake(guild_id)
        log.debug(f"{guild_id}::Setting filters to {filters}")

        payload = {}
        for _f in filters:
            payload |= _f.to_payload() if isinstance(_f, Filter) else _f
        await self.ws.set_filters(guild_id, payload)
