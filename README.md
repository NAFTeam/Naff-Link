# Naff-Link

### Note: This is very much incomplete and should not be used in production.

A [Lavalink](https://github.com/freyacodes/Lavalink) wrapper for [NAFF](https://github.com/NAFTeam/NAFF).

## Usage as of [this commit](https://github.com/NAFTeam/Naff-Link/commit/15f593aeff965b947e87a49624f60be6fc4cce4a)
```python
from naff import Client, listen, slash_command, slash_option, InteractionContext, MISSING
from naff_link.client import Client as LinkClient

class Bot(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.naff_link = MISSING

    @listen()
    async def on_startup(self):
        self.naff_link = await LinkClient.initialize(self)
        self.naff_link.connect_to("localhost", 2333, "youshallnotpass")
    
    @slash_command("play")
    @slash_option("song", "the song to play", opt_type=3, required=True)
    async def cmd_play(self, ctx: InteractionContext, song: str):
        await ctx.defer()
        
        if not ctx.voice_state:
            await self.naff_link.voice_connect(ctx.author.voice.channel, ctx.author.guild)
        
        await ctx.voice_state.play(song)
        await ctx.send("Playing {}".format(song))
```
