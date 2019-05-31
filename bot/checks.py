from discord.ext import commands
from bot.errors import Blacklisted
from .context import Context
from .errors import RequiresPrime


def check_blacklisted():
    async def predicate(ctx):
        author = await ctx.db_author
        guild = await ctx.db_guild
        blacklist = guild.updated_blacklist

        if author.id in [u.id for u in blacklist]:
            raise Blacklisted()

        return True

    return commands.check(predicate)


def prime_feature():
    async def prime_check(ctx: Context):
        if await ctx.is_prime():
            return True
        else:
            raise RequiresPrime

    return commands.check(prime_check)
