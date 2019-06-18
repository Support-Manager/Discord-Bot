import discord
import asyncio
from discord.ext import commands
from bot.utils import *
from bot import enums, errors, checks
from bot.models import graph, Scope, Language
from typing import Union


@commands.group(name='config', aliases=['set', 'configure'])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def config(ctx):
    """ This is for admins to configure the bot's behaviour on their guild. """

    if ctx.invoked_subcommand is None:
        options = [cmd.name for cmd in config.commands]
        title = ctx.translate('guided configuration')
        description = ctx.translate('this will guid you through all configurations')

        msg = None

        while True:  # config dialog loop
            action, msg = await multiple_choice(ctx, options, title, description, message=msg)

            if action is None:
                await msg.edit(content=ctx.translate("configuration dialog closed"), embed=None)
                await msg.clear_reactions()
                break

            choice = None
            converter = None
            content = None
            if action == 'prefix':
                content = 'type the new prefix'

            elif action == 'notifications':
                content = 'which channel do you wanna use as notification channel'
                converter = commands.TextChannelConverter()

            elif action == 'role':
                content = "which role do you wanna use as support role"
                converter = commands.RoleConverter()

            elif action == 'scope':
                title = ctx.translate("choose a scope as default")
                choice = await multiple_choice(ctx, [s.value for s in enums.Scope], title, message=msg)
                choice = choice[0]
                converter = Scope()

            elif action == 'language':
                title = ctx.translate("choose the language of the server")
                choice = await multiple_choice(ctx, [l.value for l in enums.Language], title, message=msg)
                choice = choice[0]
                converter = Language()

            elif action == 'category':
                content = "which category do you wanna use for channel-tickets"
                converter = commands.CategoryChannelConverter()

            elif action == 'voice':
                content = 'which category do you wanna use for voice support'
                converter = commands.CategoryChannelConverter()

            elif action == 'log':
                content = 'which channel do you wanna use for logging'
                converter = commands.TextChannelConverter()

            elif action == 'assigning':
                text = ctx.translate("do you want to enable auto-assigning")
                conf = Confirmation(ctx)
                await conf.confirm(text)

                choice = conf.confirmed

            prefix = ctx.prefix

            if content is not None:
                await msg.clear_reactions()
                note = ctx.translate("type [pfx]abort to close this dialog").format(prefix)
                await msg.edit(content=ctx.translate(content) + note, embed=None)

                def check(message):
                    return message.author.id == ctx.author.id and message.channel.id == msg.channel.id

                try:
                    choice = await ctx.bot.wait_for('message', check=check, timeout=60)
                except asyncio.TimeoutError:
                    continue
                choice = choice.content

            if choice is None or choice == prefix + 'abort':
                await msg.edit(content=ctx.translate("configuration dialog closed"), embed=None)
                await msg.clear_reactions()
                break

            if converter is not None:
                try:
                    choice = await converter.convert(ctx, choice)  # convert string to specific Object (like Channel)
                except commands.BadArgument:
                    await ctx.send(ctx.translate("invalid input"))
                    continue

            command = ctx.bot.get_command('config ' + action)
            await ctx.invoke(command, choice)


def to_be_removed(arg) -> bool:
    if type(arg) == str:
        if arg == 'remove':
            return True
        else:
            raise errors.InvalidAction
    else:
        return False


@config.error
async def config_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("configuration is only available on servers"))


@config.command(name='prefix')
async def _prefix(ctx, pfx: str = ""):
    """ This is to change the guild's cmd prefix. """

    guild = await ctx.db_guild

    if len(pfx) > enums.PrefixLength.MAX:
        await ctx.send(
            ctx.translate("prefix can't be longer than [max] characters").format(enums.PrefixLength.MAX.value)
        )

    elif len(pfx) < enums.PrefixLength.MIN:
        await ctx.send(ctx.translate("prefix must be at least [min] characters").format(enums.PrefixLength.MIN.value))

    else:
        guild.prefix = pfx
        await guild.async_push()

        await ctx.send(ctx.translate("the new prefix is [pfx]").format(pfx))


@config.command(name='notifications', aliases=['notify', 'notification', 'channel'])
async def _notifications(ctx, channel: Union[discord.TextChannel, str]):
    """ This is to set the guild's notification channel. """

    guild = await ctx.db_guild

    if to_be_removed(channel):
        guild.channel = None
        guild.push()
        await ctx.send(ctx.translate("removed"))
    else:
        guild.channel = channel.id
        await guild.async_push()
        await ctx.send(ctx.translate("i'll send ticket events in [channel]").format(channel.mention))


@config.command(name='role', aliases=['supprole', 'supporters'])
async def _role(ctx, role: Union[discord.Role, str]):
    """ This is to set the guild's support role. """

    guild = await ctx.db_guild

    if to_be_removed(role):
        guild.support_role = None
        await guild.async_push()
        await ctx.send(ctx.translate("removed"))
    else:
        guild.support_role = role.id
        await guild.async_push()
        await ctx.send(ctx.translate("i'll now notify [role] on ticket events").format(role.name))


@config.command(name='scope')
async def _default_scope(ctx, scope: Scope):
    guild = await ctx.db_guild

    guild.default_scope = scope

    await guild.async_push()

    await ctx.send(ctx.translate("all tickets will be default [scope]").format(scope))


@config.command(name='language', aliases=['lang'])
async def _language(ctx, language: Language):
    guild = await ctx.db_guild

    guild.language = language

    await guild.async_push()

    await ctx.send(ctx.translate("[language] is the default language on this server now").format(language))


@config.command(name='category')
async def _category(ctx, ticket_category: Union[discord.CategoryChannel, str]):
    guild = await ctx.db_guild

    if to_be_removed(ticket_category):
        guild.ticket_category = None
        await guild.async_push()
        await ctx.send(ctx.translate("removed"))
    else:
        guild.ticket_category = ticket_category.id
        await guild.async_push()
        await ctx.send(ctx.translate("all channel-tickets will be created in [category]").format(ticket_category.name))


@config.command(name='voice', aliases=['voice-channel'])
async def _voice(ctx, voice_category: Union[discord.CategoryChannel, str]):
    """ This is to set the guilds voice support channel. """

    guild = await ctx.db_guild

    if to_be_removed(voice_category):
        guild.voice_category = None
        await guild.async_push()
        await ctx.send(ctx.translate("removed"))
    else:
        guild.voice_category = voice_category.id
        await guild.async_push()

        await ctx.send(
            ctx.translate("i'll notify you when someone is waiting in [category]").format(voice_category.name)
        )

        channel = await guild.discord.create_voice_channel(
            name=ctx.translate("available support room"),
            category=voice_category,
            reason=ctx.translate("providing available voice support room")
        )
        await channel.edit(user_limit=2)


@config.command(name='log', aliases=['logging', 'logger'])
@checks.prime_feature()
async def _log(ctx, log_channel: Union[discord.TextChannel, str]):
    """ This is to set the guilds log channel. """

    guild = await ctx.db_guild

    if to_be_removed(log_channel):
        guild.log_channel = None
        await guild.async_push()
        await ctx.send(ctx.translate("removed"))
    else:
        guild.log_channel = log_channel.id
        await guild.async_push()
        await ctx.send(ctx.translate("i'll log my actions in [channel]").format(log_channel.mention))


@config.command(name='assigning', aliases=['auto-assigning', 'assign', 'auto-assign'])
@checks.prime_feature()
async def _assigning(ctx, enable: bool):
    """ This is to enable/disable auto-assigning for tickets. """

    guild = await ctx.db_guild

    guild.auto_assigning = enable
    await guild.async_push()

    if enable:
        await ctx.send(ctx.translate("auto-assigning enabled"))
    else:
        await ctx.send(ctx.translate("auto-assigning disabled"))
