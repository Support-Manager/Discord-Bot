import discord
from discord.ext import commands
from bot import Defaults, CONFIG


@commands.command()
async def invite(ctx):
    invite_emb = discord.Embed(
        title=ctx.translate("invite me"),
        description=ctx.translate("start getting your server managed now"),
        color=Defaults.COLOR,
        url=CONFIG['invite_url']
    )

    invite_emb.set_author(
        name="Support-Manager",
        url=CONFIG['bot_url'],
        icon_url=ctx.bot.user.avatar_url
    )

    invite_emb.set_thumbnail(
        url=ctx.bot.user.avatar_url
    )

    await ctx.send(embed=invite_emb)
