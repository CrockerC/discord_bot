import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from music_cog import music_cog
from help_cog import help_cog
from listener_cog import listener_cog

discord.Intents.all()

bot = commands.Bot(command_prefix='[')

bot.add_cog(help_cog(bot))
bot.add_cog(music_cog(bot))
bot.add_cog(listener_cog(bot))

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot.run(TOKEN)
