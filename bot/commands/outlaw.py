from bot.models import User
from discord.ext import commands
import discord
import time
from bot.utils import UnbanTimer, escaped
from bot.errors import InvalidAction
from bot.models import graph
from neo4j_connection import WarningMixin, KickMixin, BanMixin
import uuid


async def prepare_outlaw(ol, reason, user, ctx, **properties):
    setattr(ol, "uuid", uuid.uuid4().hex)
    setattr(ol, "utc", time.time())
    setattr(ol, "reason", escaped(reason))
    getattr(ol, "applies_to").add(user)
    getattr(ol, "executed_by").add(await ctx.db_author)
    getattr(ol, "executed_on").add(await ctx.db_guild)

    for p in properties:
        setattr(ol, p, properties[p])


@commands.group()
async def outlaw(ctx):
    pass


@outlaw.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, user: User, reason: str):
    db_warning = WarningMixin()
    await prepare_outlaw(db_warning, escaped(reason), user, ctx)
    graph.create(db_warning)

    conf_msg = ctx.translate("user warned")

    member = ctx.guild.get_member(user.id)

    try:
        await member.send(ctx.translate("[user] just warned you").format(
            str(ctx.author), ctx.guild.name, escaped(reason))
        )
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await ctx.send(conf_msg)
    await (await ctx.db_guild).log(ctx.translate("[user] warned [user] because of [reason]").format(
        str(ctx.author), str(member), db_warning.reason
    ))


@outlaw.command()
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
async def kick(ctx, user: User, reason: str):
    if user.id == ctx.guild.owner_id:
        raise InvalidAction("Guild owner cannot be kicked.")

    member: discord.Member = ctx.guild.get_member(user.id)

    if member is None:
        await ctx.send(ctx.translate("this user is not on this server"))
        return

    db_kick = KickMixin()
    await prepare_outlaw(db_kick, escaped(reason), user, ctx)
    graph.create(db_kick)

    conf_msg = ctx.translate("user kicked")

    try:
        await member.send(ctx.translate("[user] just kicked you").format(
            str(ctx.author), ctx.guild.name, escaped(reason))
        )
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await member.kick(reason=reason)

    await ctx.send(conf_msg)
    await (await ctx.db_guild).log(ctx.translate("[user] kicked [user] because of [reason]").format(
        str(ctx.author), str(member), db_kick.reason
    ))


@outlaw.command()
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban(ctx, user: User, reason: str, days: int = None):
    if user.id == ctx.guild.owner_id:
        raise InvalidAction("Guild owner cannot be banned.")

    db_ban = BanMixin()
    await prepare_outlaw(db_ban, escaped(reason), user, ctx, days=days)
    graph.create(db_ban)

    if days is not None:
        for_days = ctx.translate("for [days] days").format(days)
        UnbanTimer(ctx, days, user.discord, reason=ctx.translate("ban time expired"))
    else:
        for_days = ""

    conf_msg = ctx.translate("user banned").format(for_days)

    try:
        await user.discord.send(ctx.translate("[user] just banned you").format(
            str(ctx.author), ctx.guild.name, for_days, escaped(reason)
        ))
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await ctx.guild.ban(user.discord, reason=reason, delete_message_days=1)

    await ctx.send(conf_msg)
    await (await ctx.db_guild).log(ctx.translate("[user] banned [user][for days] because of [reason]").format(
        str(ctx.author), str(user.discord), for_days, db_ban.reason
    ))
