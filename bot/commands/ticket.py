from bot.utils import *
from discord.ext import commands
from bot import bot, errors, enums, checks
from bot.models import graph, Scope, User
import uuid


@bot.group(name='ticket')
@commands.guild_only()
@checks.check_blacklisted()
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    if ctx.invoked_subcommand is None:
        pass  # TODO: implement action on when it's invoked without sub-commands

    pass


@ticket.error
async def ticket_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("tickets can't be accessed via dm"))


# TODO: Rework/Rethink error system. (Throw exceptions)
@ticket.command(name='create')
async def _create(ctx, title: str, description: str="", scope: Scope=None):
    """ This is to create a support ticket. """

    guild = ctx.db_guild

    t = Ticket(ctx=ctx)

    if len(title) > enums.TitleLength.MAX:
        await ctx.send(ctx.translate("title too long").format(enums.TitleLength.MAX.value, len(title)))

    elif len(title) < enums.TitleLength.MIN:
        await ctx.send(ctx.translate("title too short").format(enums.TitleLength.MIN.value, len(title)))

    else:
        utc = time.time()

        t.title = escaped(title)

        t.description = escaped(description)

        t.state = enums.State.OPEN.value
        t.updated = utc

        author = User.from_discord_user(ctx.author)
        t.created_by.add(author, properties={'UTC': utc})

        t.located_on.add(guild)

        if scope is None:
            scope = t.guild.default_scope

        t.scope = scope

        highest_id = graph.run(
            "MATCH (t:Ticket)-[:TICKET_LOCATED_ON]->(g:Guild {id: %i}) RETURN max(t.id)" % guild.id
        ).evaluate()

        if highest_id is None:
            highest_id = 0

        t.id = highest_id + 1
        t.uuid = uuid.uuid4().hex

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

        elif t.scope_enum == enums.Scope.PRIVATE:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

            format_id = t.id

        else:
            format_id = t.id

        msg = ctx.translate("ticket created").format(format_id)

        try:
            await ctx.author.send(ctx.translate("your ticket has been created").format(t.id, guild.discord.name))
            dm_allowed = True
        except commands.BotMissingPermissions:
            dm_allowed = False

        if not dm_allowed:
            msg += '\n' + ctx.translate("please allow receiving dms")

        await ctx.send(msg)

        if t.guild.channel != ctx.channel.id:
            await notify_supporters(ctx.bot, ctx.translate('new ticket'), t.guild, embed=ticket_embed(ctx, t))


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
            t = await Ticket().convert(ctx, msg.content)
        except commands.BadArgument as e:
            await ctx.bot.on_command_error(ctx, e)  # redirects to global error handler
            return

        await ctx.invoke(_show, t)


@ticket.command(name="edit", aliases=["change", "update"])
async def _edit(ctx, t: Ticket, title: str="", description: str=None):
    if ctx.author.id != t.author.id:
        ctx.send(ctx.translate("you are not allowed to perform this action"))
        return

    if title != "":
        if len(title) > enums.TitleLength.MAX:
            await ctx.send(ctx.translate("title too long").format(enums.TitleLength.MAX.value, len(title)))
            return

        elif len(title) < enums.TitleLength.MIN:
            await ctx.send(ctx.translate("title too short").format(enums.TitleLength.MIN.value, len(title)))
            return

        else:
            t.title = escaped(title)

    t.updated = time.time()

    if description is not None:
        t.description = escaped(description)

    t.push()

    await ctx.send(ctx.translate("ticket edited"))


@ticket.command(name="append", aliases=["addinfo"])
async def _append(ctx, t: Ticket, info: str):
    new_description = f"{t.description}\n{escaped(info)}"

    edit_cmd = bot.get_command("ticket edit")
    await ctx.invoke(edit_cmd, t, description=new_description)


@ticket.command(name="respond")
async def _respond(ctx, t: Ticket, content: str):
    """ This is just a shortcut for 'response create' """

    response_create = bot.get_command("response create")
    await ctx.invoke(response_create, t, content)


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
        close_msg = ctx.translate('[user] just closed ticket [ticket]').format(ctx.author.mention, t.id)

        if response is not None:
            close_msg += f"\n```{escaped(response)}```"

        send_success = await notify_author(ctx, close_msg, t)

        if send_success == 1:
            conf_msg += ctx.translate("ticket author doesn't allow dms")

        await ctx.send(conf_msg)

        if t.guild.channel != ctx.channel.id:
            await notify_supporters(ctx.bot, close_msg, t.guild, embed=ticket_embed(ctx, t))

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

        if t.guild.channel != ctx.channel.id:
            await notify_supporters(ctx.bot,
                                    ctx.translate("[user] just reopened a ticket").format(ctx.author.mention),
                                    t.guild,
                                    ticket_embed(ctx, t))

    else:
        raise errors.MissingPermissions


@_close.error
@_reopen.error
async def _close_reopen_error(ctx, error):
    if isinstance(error.__cause__, errors.MissingPermissions):
        await ctx.send(ctx.translate("you have to be supporter or ticket author for this"))


@ticket.command(name='delete')
async def _delete(ctx, t: Ticket):
    """ This is to delete a ticket. """

    utc = time.time()

    if not ctx.may_fully_access(t):
        await ctx.send(ctx.translate("you are not allowed to perform this action"))
        return None

    conf = Confirmation(ctx)
    await conf.confirm(ctx.translate("you are attempting to delete ticket [ticket]").format(t.id))

    if conf.confirmed:
        author = User.from_discord_user(ctx.author)

        t.state_enum = enums.State.DELETED
        t.deleted_by.add(author, properties={'UTC': utc})
        t.push()

        for resp in t.get_responses():
            resp.deleted = True
            resp.deleted_by.add(author, properties={'UTC': utc})

            resp.push()

        await conf.display(ctx.translate("ticket deleted"))

        if t.scope_enum == enums.Scope.CHANNEL:
            channel = t.channel
            if channel is not None:
                await channel.delete(reason=ctx.translate("ticket has been deleted"))

    else:
        await conf.display((ctx.translate("canceled")))
