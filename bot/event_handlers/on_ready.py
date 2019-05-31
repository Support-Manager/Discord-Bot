from bot.models import Guild
import discord
import logging


logger = logging.getLogger(__name__)


def setup_ready_handler(bot):
    async def on_ready():
        logger.info(f"Logged in as: {bot.user.name}")

        for guild in bot.guilds:
            await Guild.async_from_discord_guild(guild)

        await bot.change_presence(activity=discord.Game(name="/help"))

    return on_ready
