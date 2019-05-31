import logging
import discord
from discord.ext.commands import when_mentioned_or
from .models import Guild, User, graph, Ticket, Response
from .properties import CONFIG, Defaults
from . import utils, errors
from .bot import Bot
from .context import Context


logger = logging.getLogger(__name__)


async def dynamic_prefix(b: Bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return Defaults.PREFIX

    guild = await Guild.async_from_discord_guild(msg.guild)

    return when_mentioned_or(guild.prefix)(b, msg)
