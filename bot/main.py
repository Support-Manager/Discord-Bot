from discord.ext import commands
from bot.utils import *

bot = commands.Bot(command_prefix=dynamic_prefix, pm_help=None)


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name}")

    for guild in bot.guilds:
        merge_guild(guild)

    await bot.change_presence(activity=discord.Game(name="/help"))


@bot.event
async def on_guild_join(guild):
    merge_guild(guild)


bot.load_extension('commands')

bot.run(secrets['token'])
