import logging
import discord
from .models import Guild, User, graph, Ticket, Response
from .properties import CONFIG, Defaults
from . import utils, errors
from .bot import Bot
from .context import Context


logger = logging.getLogger(__name__)


async def dynamic_prefix(bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return Defaults.PREFIX

    guild = Guild.from_discord_guild(msg.guild)

    return guild.prefix
