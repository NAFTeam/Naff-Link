import asyncio

import aiohttp
from aiohttp import ClientWebSocketResponse, ClientConnectionError
from naff import Client as NaffClient
from naff.api.gateway.gateway import GatewayClient as NaffGateway
from naff.client.utils import OverriddenJson

from naff_link import events
from . import get_logger
from .enums import OPCodes as OP
from .errors import LinkConnectionError

log = get_logger()


class WebSocket:
    def __init__(
        self,
        client,
        bot_client: NaffClient,
        naff_gateway: NaffGateway,
    ):
        self.client = client
        self.bot_client: NaffClient = bot_client
        self.naff_gateway: NaffGateway = naff_gateway

        self.__session: aiohttp.ClientSession = client.session
        self.__ws: ClientWebSocketResponse = None

    async def voice_server_update(self, guild_id, session_id, data):
        data = {
            "op": OP.voice_server_update,
            "guildId": guild_id,
            "sessionId": session_id,
            "event": data,
        }
        await self.send_json(data)

    async def play(self, guild_id, track):
        data = {"op": OP.audio_play, "guildId": str(guild_id), "track": track}
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
            "Authorization": self.client.password,
            "User-Id": str(self.bot_client.app.id),
            "Client-Name": "Naff-Link",
        }

        log.debug(f"Attempting to connect to lavalink as {headers['Client-Name']} {headers['User-Id']}")
        try:
            self.__ws = await self.__session.ws_connect(
                f"ws://{self.client.host}:{self.client.port}/", headers=headers, heartbeat=60
            )
        except ClientConnectionError as e:
            raise LinkConnectionError("Failed to connect to lavalink - are you sure lavalink is running?") from e
        except Exception as e:
            breakpoint()
        else:
            log.info("Successfully connected to lavalink")
        asyncio.create_task(self.rcv())

    async def rcv(self):
        while True:
            resp = await self.__ws.receive()

            data = OverriddenJson.loads(resp.data)

            match data["op"]:
                case "playerUpdate":
                    self.bot_client.dispatch(events.PlayerUpdate.from_dict(self.client, data))
                case "event":
                    await self.event_dispatcher(data)
                case "stats":
                    # we don't do anything with these yet
                    ...
                case _:
                    log.debug(f"Unknown payload received from lavalink:: {resp.type} :: {resp.data}")

    async def event_dispatcher(self, event: dict):
        match event["type"]:
            case "TrackStartEvent":
                self.bot_client.dispatch(events.TrackStart.from_dict(self.client, event))
            case "TrackEndEvent":
                self.bot_client.dispatch(events.TrackEnd.from_dict(self.client, event))
            case _:
                log.error(f"Unknown event (`{event['type']}`) received from lavalink :: {event}")
