import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from music_cog import music_cog
from help_cog import help_cog
from listener_cog import listener_cog
import asyncio

discord.Intents.all()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='[', intents=intents)


async def main():
    await bot.add_cog(help_cog(bot))
    await bot.add_cog(music_cog(bot))
    await bot.add_cog(listener_cog(bot))

    # GUILD = os.getenv('DISCORD_GUILD')

if __name__ == "__main__":
    asyncio.run(main())
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)
