from bot import bot
from bot.models import User
from discord.ext import commands
import discord
import time
from bot.utils import UnbanTimer
from bot.errors import InvalidAction


@bot.group()
async def outlaw(ctx):
    pass


@outlaw.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, user: User, reason: str):
    user.warned_by.add(ctx.db_author, properties={'UTC': time.time(), 'reason': reason, 'guild': ctx.guild.id})
    user.push()

    conf_msg = ctx.translate("user warned")

    member = ctx.guild.get_member(user.id)

    try:
        await member.send(ctx.translate("[user] just warned you").format(str(ctx.author), ctx.guild.name, reason))
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await ctx.send(conf_msg)


@outlaw.command()
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def kick(ctx, user: User, reason: str):
    if user.id == ctx.guild.owner_id:
        raise InvalidAction("Guild owner cannot be kicked.")

    user.kicked_by.add(ctx.db_author, properties={'UTC': time.time(), 'reason': reason, 'guild': ctx.guild.id})
    user.push()

    conf_msg = ctx.translate("user kicked")

    member: discord.Member = ctx.guild.get_member(user.id)

    try:
        await member.send(ctx.translate("[user] just kicked you").format(str(ctx.author), ctx.guild.name, reason))
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await member.kick(reason=reason)

    await ctx.send(conf_msg)


@outlaw.command()
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban(ctx, user: User, reason: str, days: int=None):
    if user.id == ctx.guild.owner_id:
        raise InvalidAction("Guild owner cannot be banned.")

    user.banned_by.add(
        ctx.db_author,
        properties={'UTC': time.time(), 'reason': reason, 'days': days, 'guild': ctx.guild.id}
    )

    user.push()

    if days is not None:
        for_days = ctx.translate("for [days] days").format(days)
    else:
        for_days = ""

    conf_msg = ctx.translate("user banned").format(for_days)

    member: discord.Member = ctx.guild.get_member(user.id)

    try:
        await member.send(ctx.translate("[user] just banned you").format(str(ctx.author), for_days, reason))
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await member.ban(reason=reason, delete_message_days=1)

    UnbanTimer(days, member, reason=ctx.translate("ban time expired"))

    await ctx.send(conf_msg)
