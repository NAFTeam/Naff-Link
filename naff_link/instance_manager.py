import random
import re
from functools import cached_property
from typing import TYPE_CHECKING

from naff import Guild, Snowflake_Type, to_snowflake

from naff_link import get_logger
from naff_link.events import StatsUpdate
from naff_link.models.instance import Instance
from naff_link.models.stats import Stats

if TYPE_CHECKING:
    from naff_link.client import Client

log = get_logger()


class InstanceManager:
    def __init__(self, link_client: "Client"):
        self.instances: list[Instance] = []
        self._link_client: "Client" = link_client

        self._instance_by_guild: dict[Snowflake_Type, Instance] = {}
        self._cached_regions: list[str] = []
        self._vc_endpoints: dict[int, str] = {}

    async def connect_to_instance(self, host, port, password, *, region: str = None):
        instance = Instance.create(self._link_client, host, port, password, region=region)
        await instance.connect()
        self.instances.append(instance)

        # update known regions from discord
        self._cached_regions = [r["id"] for r in await self._link_client.naff.http.list_voice_regions()]
        if region and region not in self._cached_regions:
            raise ValueError(
                f"Region {region} is not a valid region - please refer to the discord API docs for valid regions"
            )

    def get_instance_by_guild(self, guild: Guild | Snowflake_Type) -> Instance:
        g_id = to_snowflake(guild)
        region = None

        if g_id in self._instance_by_guild:
            # return cached instance if available
            return self._instance_by_guild[g_id]

        for instance in self.available_instances:
            # check if any instance has the guild
            if g_id in instance.guild_ids:
                self._instance_by_guild[g_id] = instance
                return instance

        if endpoint := self._vc_endpoints.get(g_id, None):
            # we have an endpoint for this guild, so we can use that to find the instance
            region = re.findall(r"^(\w.*?)\d", endpoint)[0]

        instance = self.find_ideal_instance(region)
        self._instance_by_guild[g_id] = instance
        return instance

    def find_ideal_instance(self, region: str | None) -> Instance:
        """
        Finds the ideal instance to use for the given region.
        """
        instances = {}

        if region:
            if region not in self._cached_regions:
                raise ValueError(
                    f"Region {region} is not a valid region - please refer to the discord API docs for valid regions"
                )
            instances = self.instances_by_region.get(str(region), self.available_instances)
        if not instances:
            instances = self.available_instances

        best = min(instances, key=lambda i: i.load_penalty)
        log.debug(f"Selecting {best.name} as ideal instance for region `{region}` :: penalty: {best.load_penalty}")
        return best

    @property
    def instances_by_region(self) -> dict[str, list[Instance]]:
        out = {}
        for instance in self.instances:
            if instance.region not in out:
                out[str(instance.region)] = []
            out[str(instance.region)].append(instance)
        return out

    @property
    def available_instances(self) -> list[Instance]:
        return [i for i in self.instances if i.is_connected]

    async def voice_server_update(self, guild: Snowflake_Type, session_id, event_data):
        guild_id = to_snowflake(guild)
        self._vc_endpoints[guild_id] = event_data["endpoint"]
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.voice_server_update(guild_id, session_id, event_data)

    async def play(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.play(guild_id, *args, **kwargs)

    async def stop(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.stop(guild_id, *args, **kwargs)

    async def pause(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.pause(guild_id, *args, **kwargs)

    async def resume(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.pause(guild_id, *args, **kwargs)

    async def seek(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.seek(guild_id, *args, **kwargs)

    async def volume(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.volume(guild_id, *args, **kwargs)

    async def set_filters(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.set_filters(guild_id, *args, **kwargs)

    async def set_equalizer(self, guild: Snowflake_Type, *args, **kwargs):
        guild_id = to_snowflake(guild)
        instance = self.get_instance_by_guild(guild_id)

        return await instance.ws.set_equalizer(guild_id, *args, **kwargs)

    async def resolve_track(self, *args, **kwargs):
        #  request from the instance with the lowest load
        instance = min(self.instances, key=lambda i: i.load_penalty)

        return await instance._rest.resolve_track(*args, **kwargs)

    async def decode_track(self, *args, **kwargs):
        #  request from the instance with the lowest load
        instance = min(self.instances, key=lambda i: i.load_penalty)

        return await instance._rest.decode_track(*args, **kwargs)
