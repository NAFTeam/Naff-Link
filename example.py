from lavalink import TrackStartEvent
from naff import Client, listen, InteractionContext, slash_command
from naff.api.events import VoiceStateUpdate

from naff_link import NaffLink


class Bot(Client):
    naff_link: NaffLink

    def __init__(self):
        super().__init__()

        self.load_extension("naff_link")

    @listen()
    async def on_startup(self):
        print(f"Logged in as {self.user.username}")

        self.naff_link.add_node("localhost", 2333, "youshallnotpass", "eu")
        await self.naff_link.ready.wait()

        player = await self.naff_link.connect_to_vc(
            701347683591389185, 1032194696891609128
        )

        results = await self.naff_link.get_tracks(
            "https://www.youtube.com/watch?v=jfKfPfyJRdk"
        )
        await player.play(results.tracks[0])

    @slash_command("stop", description="Stop the player")
    async def stop(self, ctx: InteractionContext):
        player = self.naff_link.get_player(ctx.guild)
        await player.stop()
        await ctx.send("Stopped the player")

    @listen()
    async def on_track_start_event(self, event):
        link_event: TrackStartEvent = event.link_event

        print(f"Now playing `{link_event.track.title}` in {link_event.player.guild_id}")

    @listen()
    async def on_voice_state_update(self, event: VoiceStateUpdate):
        # Disconnect from the voice channel if the bot is the only one left
        if not event.after:
            # get the latest state of the channel
            channel = self.get_channel(event.before.channel.id)

            if len(channel.voice_members) == 1:
                if channel.voice_members[0].id == self.user.id:
                    await self.naff_link.disconnect(event.before.guild)


if __name__ == "__main__":
    bot = Bot()
    bot.start(TOKEN)
