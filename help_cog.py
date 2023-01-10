import discord
from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.text_channel_text = []
        self.help_message = """
```
General commands:

[help - displays all available commands
[play <keywords> - finds youtube video using keywords and adds it to the queue
[queue - displays the current music queue
[skip - skip current song being played
[clear - stops the current song and clears the queue
[leave - disconnects bot from channel
[pause - pauses current song
[resume - unpauses if paused
```

"""

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            print(guild)
            if str(guild) != "ODSTjoker's server":
                continue
            for channel in guild.text_channels:
                # todo, make this only respond to the bot request channel... maybe
                # todo, or maybe just my personal one
                self.text_channel_text.append(channel)
        await self.send_to_all(self.help_message)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_text:
            await text_channel.send(msg)

    @commands.command(name="m_help", help="displays all available commands")
    async def help(self, ctx):
        print("here")
        # sends help message to current channel (same as command)
        await ctx.send(self.help_message)

