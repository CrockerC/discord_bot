import discord
from discord.ext import commands
from discord import client
import asyncio
from misc import dlog


class listener_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time = 0
        self.channel = None
        self.voice = None
        self.idle_timeout = 600

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        dlog("Got voice channel user update")

        if after.channel is not None:
            voice = after.channel.guild.voice_client
        elif before.channel is not None:
            voice = before.channel.guild.voice_client
        else:
            voice = None

        self.voice = voice  # current state of voice

        if voice is None:
            return

        member_ids = list(voice.channel.voice_states.keys())

        # set the current channel
        if self.bot.user.id in member_ids:
            self.channel = voice.channel.id

        if member.id == self.bot.user.id:
            dlog("Bot entering sleep loop")
            while True:
                await asyncio.sleep(1)
                self.time = self.time + 1
                if voice.is_playing() and not voice.is_paused():
                    self.time = 0
                if self.time == self.idle_timeout:
                    dlog("Idle for {} minutes, disconnecting".format(self.idle_timeout / 60))
                    self.bot.cogs['music_cog'].music_queue = []
                    self.bot.cogs['music_cog'].vc.stop()
                    await voice.disconnect()
                if self.voice is None:
                    return

        # if the bot is alone, leave
        if len(member_ids) == 1:
            self.bot.cogs['music_cog'].music_queue = []
            self.bot.cogs['music_cog'].vc.stop()
            dlog("Nobody in channel, disconnecting")
            await voice.disconnect()



