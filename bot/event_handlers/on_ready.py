from bot.models import Guild
import discord
import logging
import asyncio


logger = logging.getLogger(__name__)


def setup_ready_handler(bot):
    async def on_ready():
        logger.info(f"Logged in as: {bot.user.name}")

        loop = asyncio.get_event_loop()

        tasks = [loop.create_task(Guild.async_from_discord_guild(guild)) for guild in bot.guilds]
        await asyncio.wait(tasks, loop=loop, return_when=asyncio.ALL_COMPLETED)

        await bot.change_presence(activity=discord.Game(name="/help"))

    return on_ready
