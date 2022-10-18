import asyncio
from typing import TYPE_CHECKING

import aiohttp
from aiohttp import ClientWebSocketResponse, ClientConnectionError, WSMsgType
from naff import Client as NaffClient
from naff.api.gateway.gateway import GatewayClient as NaffGateway
from naff.client.utils import OverriddenJson

from naff_link import events
from naff_link import get_logger
from naff_link.enums import OPCodes as OP
from naff_link.errors import LinkConnectionError

if TYPE_CHECKING:
    from naff_link.models.instance import Instance

log = get_logger()


class WebSocket:
    def __init__(
        self,
        client,
        bot_client: NaffClient,
        naff_gateway: NaffGateway,
        instance: "Instance",
    ):
        self.client = client
        self.bot_client: NaffClient = bot_client
        self.naff_gateway: NaffGateway = naff_gateway
        self.__instance: "Instance" = instance

        self.__session: aiohttp.ClientSession = client.session
        self.__ws: ClientWebSocketResponse = None

    @property
    def is_connected(self) -> bool:
        return self.__ws is not None and not self.__ws.closed

    async def voice_server_update(self, guild_id, session_id, data):
        data = {
            "op": OP.voice_server_update,
            "guildId": guild_id,
            "sessionId": session_id,
            "event": data,
        }
        await self.send_json(data)

    async def play(
        self, guild_id, track, *, start_time: float = 0, end_time: float = None, volume: int = None, pause: bool = False
    ):
        data = {"op": OP.audio_play, "guildId": str(guild_id), "track": track, "startTime": start_time, "pause": pause}

        if end_time is not None:
            data["endTime"] = end_time
        if volume is not None:
            data["volume"] = volume

        await self.send_json(data)

    async def stop(self, guild_id):
        await self.send_json({"op": OP.audio_stop, "guildId": str(guild_id)})

    async def pause(self, guild_id, pause: bool = True):
        await self.send_json({"op": OP.audio_pause, "guildId": str(guild_id), "pause": pause})

    async def seek(self, guild_id, position: int):
        await self.send_json({"op": OP.audio_seek, "guildId": str(guild_id), "position": position})

    async def volume(self, guild_id, volume: int):
        await self.send_json({"op": OP.audio_volume, "guildId": str(guild_id), "volume": volume})

    async def set_equalizer(self, guild_id, payload):
        await self.send_json({"op": OP.equalizer, "guildId": str(guild_id), "bands": payload})

    async def set_filters(self, guild_id, payload):
        await self.send_json({"op": OP.filters, "guildId": str(guild_id)} | payload)

    async def send_json(self, data: dict):
        log.debug(f"Sending data to lavalink :: {data}")
        await self.__ws.send_json(data)

    async def connect(self):
        headers = {
            "Authorization": self.__instance.password,
            "User-Id": str(self.bot_client.app.id),
            "Client-Name": "Naff-Link",
        }

        log.debug(f"Attempting to connect to lavalink as {headers['Client-Name']} {headers['User-Id']}")
        try:
            self.__ws = await self.__session.ws_connect(
                f"ws://{self.__instance.host}:{self.__instance.port}/", headers=headers, heartbeat=60
            )
        except ClientConnectionError as e:
            raise LinkConnectionError("Failed to connect to lavalink - are you sure lavalink is running?") from e
        except Exception as e:
            breakpoint()
        else:
            log.info("Successfully connected to lavalink")
        asyncio.create_task(self.rcv())

    async def rcv(self):
        async for message in self.__ws:
            data = OverriddenJson.loads(message.data)

            match data["op"]:
                case "playerUpdate":
                    self.bot_client.dispatch(events.PlayerUpdate.from_dict(self.client, data))
                case "event":
                    await self.event_dispatcher(data)
                case "stats":
                    self.__instance.update_stats(data)
                case _:
                    log.debug(f"Unknown payload received from lavalink:: {message.type} :: {message.data}")
        log.warning(f"{self.__instance.name}:: Websocket Disconnected")

    async def event_dispatcher(self, event: dict):
        match event["type"]:
            case "TrackStartEvent":
                self.bot_client.dispatch(events.TrackStart.from_dict(self.client, event))
            case "TrackEndEvent":
                self.bot_client.dispatch(events.TrackEnd.from_dict(self.client, event))
            case "TrackStuckEvent":
                self.bot_client.dispatch(events.TrackStuck.from_dict(self.client, event))
            case _:
                log.error(f"Unknown event (`{event['type']}`) received from lavalink :: {event}")
