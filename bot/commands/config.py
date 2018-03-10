from discord.ext import commands
from bot.utils import *
from ._setup import bot
from bot import converters

PREFIX_MIN_LEN = 1
PREFIX_MAX_LEN = 3


@bot.group(name='config', aliases=['set', 'configure'])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def config(ctx):
    """ This is for admins to configure the bot's behaviour on their guild. """

    if ctx.invoked_subcommand is None:
        await ctx.send("What would you like to configure?")  # TODO: create guided configuration


@config.error
async def config_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Configuration is only available on servers.")

    else:
        logger.error(error)


@config.command(name='prefix')
async def _prefix(ctx, pfx: str = ""):
    """ This is to change the guild's cmd prefix. """

    if len(pfx) > PREFIX_MAX_LEN:
        await ctx.send(f"Prefix can't be longer than {PREFIX_MAX_LEN} characters.")

    elif len(pfx) < PREFIX_MIN_LEN:
        await ctx.send(f"Prefix must be at least {PREFIX_MIN_LEN} character.")

    else:
        guild = Guild()
        guild.id = ctx.guild.id
        graph.pull(guild)
        guild.prefix = pfx
        graph.push(guild)

        await ctx.send(f"Okay, your new prefix is: `{pfx}`.")


@config.command(name='channel')
async def _channel(ctx, channel: discord.TextChannel):
    """ This is to set the guild's support channel. """

    guild = Guild.select(graph, ctx.guild.id).first()
    guild.channel = channel.id
    graph.push(guild)

    await ctx.send(f"Okay, I'll send ticket events in {channel.mention} :white_check_mark:")


@config.command(name='role', aliases=['supprole', 'supporters'])
async def _role(ctx, role: discord.Role):
    """ This is to set the guild's support role. """

    guild = Guild.select(graph, ctx.guild.id).first()
    guild.support_role = role.id
    graph.push(guild)

    await ctx.send(f"Okay, I'll now notify `{role.name}` role on ticket events :white_check_mark:")


@_channel.error
@_role.error
async def _config_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("You have to mention it.")


@config.command(name='scope')
async def _default_scope(ctx, scope: converters.Scope):
    guild = Guild.select(graph, ctx.guild.id).first()

    guild.default_scope = scope

    graph.push(guild)

    await ctx.send(f"Okay, all tickets will be default `{scope}`.")


@_default_scope.error
async def _scope_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(error)

