from discord.ext import commands
from bot import errors, utils, properties
from bot.models import User
import time
import discord
from copy import deepcopy


@commands.group()
async def blacklist(ctx):
    if ctx.db_guild.support_role not in [r.id for r in ctx.author.roles]:
        if not ctx.author.guild_permissions.administrator:
            raise errors.MissingPermissions

    if ctx.invoked_subcommand is None:
        await ctx.invoke(ctx.bot.get_command('blacklist show'))


@blacklist.command(name="add", aliases=["append"])
async def _add(ctx, user: User, reason: str, days: int=None):
    user.blacklisted_on.add(
        ctx.db_guild,
        properties={'UTC': time.time(), 'reason': utils.escaped(reason), 'days': days, 'guild': ctx.guild.id}
    )

    user.push()

    if days is not None:
        for_days = ctx.translate("for [days] days").format(days)
    else:
        for_days = ""

    conf_msg = ctx.translate("user blacklisted").format(for_days)

    member: discord.Member = ctx.guild.get_member(user.id)

    try:
        await member.send(ctx.translate("[user] just blacklisted you").format(str(ctx.author), str(ctx.guild), reason))
    except discord.Forbidden:
        warning_note = ctx.translate("but user doesn't allow direct messages")
        conf_msg = f"{conf_msg}\n{warning_note}"

    await ctx.send(conf_msg)
    await ctx.db_guild.log(ctx.translate("[user] blacklisted [user] [reason]").format(
        str(ctx.author), str(member), utils.escaped(reason)
    ))


@blacklist.command(name="remove")
async def _remove(ctx, user: User):
    guild = ctx.db_guild

    if user.id not in [u.id for u in guild.updated_blacklist]:
        await ctx.send(ctx.translate("user not in blacklist"))

    else:
        guild.blacklist.remove(user)
        guild.push()

        await ctx.send(ctx.translate("removed user from blacklist"))
        await ctx.db_guild.log(ctx.translate("[user] removed [user] from blacklist").format(
            str(ctx.author), str(user.discord)
        ))


@blacklist.command(name="show")
async def _show(ctx):
    blacklist_emb = discord.Embed(
        title="Blacklist",
        color=properties.Defaults.COLOR
    )
    blacklist_emb.set_author(
        name=ctx.guild.name,
        icon_url=ctx.guild.icon_url
    )

    sub_lists = utils.EmbedPaginator.generate_sub_lists(list(ctx.db_guild.updated_blacklist))

    if len(sub_lists) == 1 and len(sub_lists[0]) == 0:
        await ctx.send(ctx.translate("blacklist is empty"))
        return

    pages = []
    for sub_list in sub_lists:
        page = deepcopy(blacklist_emb)  # copy by value not reference
        for user in sub_list:
            discord_user = ctx.bot.get_user(user.id)
            page.add_field(
                name=f"{str(discord_user)}",
                value=ctx.db_guild.blacklist.get(user, 'reason'),
                inline=False
            )
        pages.append(page)

    paginator = utils.EmbedPaginator(ctx, pages)
    await paginator.run()
