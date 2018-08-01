from bot.utils import *
from ._setup import bot
from discord.ext import commands
from bot import errors, logger, enums
from bot.models import graph, Scope, User, Guild


@bot.group(name='ticket')
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    # TODO: implement action on when it's invoked without subcommands

    pass


# TODO: Rework/Rethink error system. (Throw exceptions)
@ticket.command(name='create')
@commands.guild_only()
async def _create(ctx, title: str, description: str=None, scope: Scope=None):
    """ This is to create a support ticket. """

    guild = ctx.db_guild

    t = Ticket()

    if len(title) > enums.TitleLength.MAX:
        await ctx.send(ctx.translate("title too long").format(enums.TitleLength.MAX.value, len(title)))

    elif len(title) < enums.TitleLength.MIN:
        await ctx.send(ctx.translate("title too short").format(enums.TitleLength.MIN.value, len(title)))

    else:
        utc = time.time()

        t.title = escaped(title)

        t.description = escaped(description)

        t.state = "open"
        t.updated = utc

        author = User.from_discord_user(ctx.author)
        t.created_by.add(author, properties={'UTC': utc})

        t.located_on.add(guild)

        if scope is None:
            scope = t.guild.default_scope

        t.scope = scope

        highest_id = graph.run(
            "MATCH (t:Ticket)-[:LOCATED_ON]->(g:Guild {id: %i}) RETURN max(t.id)" % guild.id
        ).evaluate()

        if highest_id is None:
            highest_id = 0

        t.id = highest_id + 1

        graph.create(t)

        # create text channel (and category if not exist yet) for channel ticket
        if t.scope_enum == enums.Scope.CHANNEL:
            supporter = discord.utils.get(guild.discord.roles, id=guild.support_role)
            if supporter is None:
                supporter = guild.discord.owner

            overwrites = {
                guild.discord.default_role:
                    discord.PermissionOverwrite(read_messages=False),
                guild.discord.me:
                    discord.PermissionOverwrite(manage_messages=True, add_reactions=True),
                supporter:
                    discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if guild.category_channel is None:
                category = await guild.discord.create_category(
                    ctx.translate("support tickets"),
                    overwrites=overwrites,
                    reason=ctx.translate("first channel-ticket has been created")
                )
                guild.category_channel = category.id
                guild.push()
            else:
                category = guild.discord.get_channel(guild.category_channel)

            overwrites[author.discord] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await guild.discord.create_text_channel(
                str(t.id),
                overwrites=overwrites,
                category=category,
                reason=ctx.translate("new channel-ticket has been created")
            )
            await channel.edit(
                topic=t.title
            )
            await channel.send(embed=ticket_embed(ctx, t))
            format_id = channel.mention

        else:
            format_id = t.id

        msg = ctx.translate("ticket created").format(format_id)

        try:
            await ctx.author.send(ctx.translate("your ticket has been created").format(t.id))
            dm_allowed = True
        except commands.BotMissingPermissions:
            dm_allowed = False

        if not dm_allowed:
            msg += '\n' + ctx.translate("please allow receiving dms")

        await ctx.send(msg)

        await notify_supporters(ctx, ctx.translate('new ticket'), t)


@_create.error
async def _creation_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("tickets can't be created via dm"))

    elif isinstance(error, commands.BadArgument):
        await ctx.send(error)

    raise error


@ticket.command(name="show")
async def _show(ctx, t: Ticket):
    """ This is to see a specific support ticket. """

    # checking scopes (permissions)
    if ctx.author.id == t.author.id:
        pass

    elif t.scope_enum != enums.Scope.CHANNEL and ctx.channel != t.channel and not ctx.may_fully_access(t):
        await ctx.send(ctx.translate('this is a channel ticket'))
        return None

    elif t.scope_enum == enums.Scope.PRIVATE:
        if t.guild.support_role not in [role.id for role in ctx.author.roles]:
            ctx.send(ctx.translate('this is a private ticket'))
            return None

    viewer = TicketViewer(ctx, t)
    await viewer.run()


@_show.error
async def _show_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(ctx.translate('which ticket do you wanna see'))

        def check(m):
            return m.author == ctx.author

        msg = await bot.wait_for('message', check=check)

        try:
            ticket_id = int(msg.content)
        except ValueError:
            return 0

        await ctx.invoke(_show, Ticket.get(ticket_id))

    elif isinstance(error, commands.BadArgument):
        await ctx.send(error)

    else:
        logger.error(error)


@ticket.command(name='close')
async def _close(ctx, t: Ticket, response=None):
    """ This is to close a specific support ticket. """

    if ctx.may_fully_access(t):
        if t.state_enum == enums.State.CLOSED:
            await ctx.send(ctx.translate('this ticket is already closed'))
            return None

        utc = time.time()

        t.state = enums.State.CLOSED.value

        user = User.from_discord_user(ctx.author)
        t.closed_by.add(user, properties={'UTC': utc})

        t.updated = utc

        graph.push(t)

        conf_msg = ctx.translate('ticket closed')
        close_msg = ctx.translate('[user] just closed ticket [ticket]').format(str(ctx.author), t.id)

        if response is not None:
            close_msg += f"\n```{escaped(response)}```"

        send_success = await notify_author(ctx, close_msg, t)

        if send_success == 1:
            conf_msg += ctx.translate("ticket author doesn't allow dms")

        await ctx.send(conf_msg)

        await notify_supporters(ctx, close_msg, t, embed=False)

        if t.scope_enum == enums.Scope.CHANNEL:
            channel = t.channel
            if channel is not None:
                await channel.delete(reason=ctx.translate("ticket has been closed"))

    else:
        raise errors.MissingPermissions


@ticket.command(name='reopen')
async def _reopen(ctx, t: Ticket):
    """ This is to reopen a specific support ticket. """

    if ctx.may_fully_access(t):
        if t.state_enum != enums.State.CLOSED:
            await ctx.send(ctx.translate("this ticket is not closed"))
            return None

        utc = time.time()

        t.state = enums.State.REOPENED.value

        user = User.from_discord_user(ctx.author)
        t.reopened_by.add(user, properties={'UTC': utc})

        t.updated = utc

        graph.push(t)

        if t.scope_enum == enums.Scope.CHANNEL:
            category = t.guild.discord.get_channel(t.guild.category_channel)

            channel = await t.guild.discord.create_text_channel(
                str(t.id),
                overwrites={t.author.discord: discord.PermissionOverwrite(read_messages=True, send_messages=True)},
                category=category,
                reason=ctx.translate("channel-ticket has been reopened")
            )
            await channel.edit(
                topic=t.title,
                sync_permissions=True
            )

        await ctx.send(ctx.translate("ticket reopened"))

        await notify_supporters(ctx, ctx.translate("[user] reopened a ticket").format(ctx.author.mention), t)

    else:
        raise errors.MissingPermissions


@_close.error
@_reopen.error
async def _close_reopen_error(ctx, error):
    if isinstance(error.__cause__, errors.MissingPermissions):
        await ctx.send(ctx.translate("you have to be supporter or ticket author for this"))

    else:
        logger.error(error.__cause__, error)
