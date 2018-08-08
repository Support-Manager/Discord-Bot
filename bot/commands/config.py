from discord.ext import commands
from bot.utils import *
from bot import bot, enums
from bot.models import graph, Scope, Language


@bot.group(name='config', aliases=['set', 'configure'])
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

            elif action == 'channel':
                content = 'which channel do you wanna use as support channel'
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

            prefix = ctx.prefix

            if content is not None:
                await msg.clear_reactions()
                note = ctx.translate("type [pfx]abort to close this dialog").format(prefix)
                await msg.edit(content=ctx.translate(content) + note, embed=None)

                def check(message):
                    return message.author.id == ctx.author.id and message.channel.id == msg.channel.id

                try:
                    choice = await bot.wait_for('message', check=check, timeout=60)
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

            command = bot.get_command('config ' + action)
            await ctx.invoke(command, choice)


@config.error
async def config_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("configuration is only available on servers"))


@config.command(name='prefix')
async def _prefix(ctx, pfx: str = ""):
    """ This is to change the guild's cmd prefix. """

    guild = ctx.db_guild

    if len(pfx) > enums.PrefixLength.MAX:
        await ctx.send(
            ctx.translate("prefix can't be longer than [max] characters").format(enums.PrefixLength.MAX.value)
        )

    elif len(pfx) < enums.PrefixLength.MIN:
        await ctx.send(ctx.translate("prefix must be at least [min] characters").format(enums.PrefixLength.MIN.value))

    else:
        guild.prefix = pfx
        graph.push(guild)

        await ctx.send(ctx.translate("the new prefix is [pfx]").format(pfx))


@config.command(name='channel')
async def _channel(ctx, channel: discord.TextChannel):
    """ This is to set the guild's support channel. """

    guild = ctx.db_guild
    guild.channel = channel.id
    graph.push(guild)

    await ctx.send(ctx.translate("i'll send ticket events in [channel]").format(channel.mention))


@config.command(name='role', aliases=['supprole', 'supporters'])
async def _role(ctx, role: discord.Role):
    """ This is to set the guild's support role. """

    guild = ctx.db_guild
    guild.support_role = role.id
    guild.push()

    await ctx.send(ctx.translate("i'll now notify [role] on ticket events").format(role.name))


@config.command(name='scope')
async def _default_scope(ctx, scope: Scope):
    guild = ctx.db_guild

    guild.default_scope = scope

    guild.push()

    await ctx.send(ctx.translate("all tickets will be default [scope]").format(scope))


@config.command(name='language', aliases=['lang'])
async def _language(ctx, language: Language):
    guild = ctx.db_guild

    guild.language = language

    guild.push()

    await ctx.send(ctx.translate("[language] is the default language on this server now").format(language))


@config.command(name='category')
async def _category(ctx, category_channel: discord.CategoryChannel):
    guild = ctx.db_guild

    guild.category_channel = category_channel.id

    guild.push()

    await ctx.send(ctx.translate("all channel-tickets will be created in [category]").format(category_channel.name))
