import discord
from discord.ext import commands
from bot import Defaults, CONFIG


@commands.command()
async def vote(ctx):
    vote_emb = discord.Embed(
        title=ctx.translate("vote for this bot"),
        description=ctx.translate("vote for this bot on dbl"),
        color=Defaults.COLOR,
        url=CONFIG['vote_url']
    )

    vote_emb.set_author(
        name="DBL - Discord Bot List",
        url="https://discordbots.org/bot/support",
        icon_url=CONFIG['dbl_logo']
    )

    vote_emb.set_thumbnail(
        url=ctx.bot.user.avatar_url
    )

    await ctx.send(embed=vote_emb)
