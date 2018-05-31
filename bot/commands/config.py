from discord.ext import commands
from bot.utils import *
from ._setup import bot
from bot import converters


@bot.group(name='config', aliases=['set', 'configure'])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def config(ctx):
    """ This is for admins to configure the bot's behaviour on their guild. """

    if ctx.invoked_subcommand is None:
        guild = get_guild(ctx.guild)
        language = guild.language

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
                choice = await multiple_choice(ctx, CONFIG['scopes'], title, message=msg)
                choice = choice[0]
                converter = converters.Scope()

            elif action == 'language':
                title = ctx.translate("choose the language of the server")
                choice = await multiple_choice(ctx, CONFIG['languages'], title, message=msg)
                choice = choice[0]
                converter = converters.Language()

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
    language = get_guild(ctx.guild).language

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("configuration is only available on servers"))

    elif isinstance(error, commands.CommandError):
        logger.debug(error.__traceback__)
        await ctx.send(ctx.translate("you have to be admin for that"))

    else:
        logger.error(error)


@config.command(name='prefix')
async def _prefix(ctx, pfx: str = ""):
    """ This is to change the guild's cmd prefix. """

    guild = get_guild(ctx.guild)
    language = guild.language

    min_len = CONFIG['prefix_min_len']
    max_len = CONFIG['prefix_max_len']

    if len(pfx) > max_len:
        await ctx.send(ctx.translate("prefix can't be longer than [max] characters").format(max_len))

    elif len(pfx) < min_len:
        await ctx.send(ctx.translate("prefix must be at least [min] characters").format(min_len))

    else:
        guild.prefix = pfx
        graph.push(guild)

        await ctx.send(ctx.translate("the new prefix is [pfx]").format(pfx))


@config.command(name='channel')
async def _channel(ctx, channel: discord.TextChannel):
    """ This is to set the guild's support channel. """

    guild = Guild.select(graph, ctx.guild.id).first()
    guild.channel = channel.id
    graph.push(guild)

    await ctx.send(ctx.translate("i'll send ticket events in [channel]").format(channel.mention))


@config.command(name='role', aliases=['supprole', 'supporters'])
async def _role(ctx, role: discord.Role):
    """ This is to set the guild's support role. """

    guild = Guild.select(graph, ctx.guild.id).first()
    guild.support_role = role.id
    graph.push(guild)

    await ctx.send(ctx.translate("i'll now notify [role] on ticket events").format(role.name))


@_channel.error
@_role.error
async def _config_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(ctx.translate("role not found"))


@config.command(name='scope')
async def _default_scope(ctx, scope: converters.Scope):
    guild = Guild.select(graph, ctx.guild.id).first()

    guild.default_scope = scope

    graph.push(guild)

    await ctx.send(ctx.translate("all tickets will be default [scope]").format(scope))


@_default_scope.error
async def _scope_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(error)


@config.command(name='language', aliases=['lang'])
async def _language(ctx, language: converters.Language):
    guild = Guild.select(graph, ctx.guild.id).first()

    guild.language = language

    graph.push(guild)

    await ctx.send(ctx.translate("[language] is the default language on this server now").format(language))


@_language.error
async def _language_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(error)
