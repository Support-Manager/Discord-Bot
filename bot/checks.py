from discord.ext import commands
from bot.errors import Blacklisted


def check_blacklisted():
    async def predicate(ctx):
        author = ctx.db_author
        guild = ctx.db_guild
        blacklist = guild.updated_blacklist

        if author.id in [u.id for u in blacklist]:
            raise Blacklisted()

        return True

    return commands.check(predicate)
