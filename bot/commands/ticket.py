from bot.utils import *
from ._setup import bot
from discord.ext import commands
from bot import converters, errors


@bot.group(name='ticket')
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    # TODO: implement action on when it's invoked without subcommands

    pass


# TODO: Rework/Rethink error system. (Throw exceptions)
@ticket.command(name='create')
@commands.guild_only()
async def _create(ctx, title: str, description: str=None, scope: converters.Scope=None):
    """ This is to create a support ticket. """

    guild = ctx.db_guild

    t = Ticket()

    if len(title) > CONFIG["title_max_len"]:
        await ctx.send(ctx.translate("title too long").format(CONFIG["title_max_len"], len(title)))

    elif len(title) < CONFIG["title_min_len"]:
        await ctx.send(ctx.translate("title too short").format(CONFIG["title_min_len"], len(title)))

    else:
        utc = time.time()

        t.title = escaped(title)

        t.description = escaped(description)

        t.state = "open"
        t.updated = utc

        author = get_user(ctx.author)
        t.created_by.add(author, properties={'UTC': utc})

        t.located_on.add(guild)

        if scope is None:
            scope = t.guild.default_scope

        t.scope = scope

        highest_id = graph.run("MATCH (t: Ticket) RETURN max(t.id)").evaluate()
        if highest_id is None:
            highest_id = 0

        t.id = highest_id + 1

        graph.create(t)

        try:
            await ctx.author.send(ctx.translate("your ticket has been created").format(t.id))
            dm_allowed = True
        except commands.BotMissingPermissions:
            dm_allowed = False

        msg = ctx.translate("ticket created").format(t.id)

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
async def _show(ctx, t: converters.Ticket):
    """ This is to see a specific support ticket. """

    # checking scopes (permissions)
    if ctx.author.id == t.author.id:
        pass

    elif t.scope != 'public' and t.guild.id != ctx.guild.id:
        await ctx.send(ctx.translate('this is a local ticket of another guild'))
        return None

    elif t.scope == 'private':
        if t.guild.support_role not in [role.id for role in ctx.author.roles]:
            ctx.send(ctx.translate('this is a private ticket'))
            return None

    """
    emb = ticket_embed(ctx, t)

    await ctx.send(embed=emb)
    # TODO: extend to show responses
    """

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

        await ctx.invoke(_show, await converters.Ticket().convert(ctx, ticket_id))

    elif isinstance(error, commands.BadArgument):
        await ctx.send(error)

    else:
        logger.error(error)


@ticket.command(name='close')
async def _close(ctx, t: converters.Ticket, response=None):
    """ This is to close a specific support ticket. """

    if is_author_or_supporter(ctx, t):
        language = get_guild(ctx.guild).language

        if t.state == 'closed':
            await ctx.send(ctx.translate('this ticket is already closed'))
            return None

        utc = time.time()

        t.state = 'closed'

        user = get_user(ctx.author)
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

        await notify_supporters(ctx, close_msg, t, embed=False)

    else:
        raise errors.MissingPermissions


@ticket.command(name='reopen')
async def _reopen(ctx, t: converters.Ticket):
    """ This is to reopen a specific support ticket. """

    if is_author_or_supporter(ctx, t):
        language = get_guild(ctx.guild).language

        if t.state != 'closed':
            await ctx.send(ctx.translate("this ticket is not closed"))
            return None

        utc = time.time()

        t.state = 'reopened'

        user = get_user(ctx.author)
        t.reopened_by.add(user, properties={'UTC': utc})

        t.updated = utc

        graph.push(t)

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
        logger.error(error)
