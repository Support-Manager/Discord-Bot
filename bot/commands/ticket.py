from bot.utils import *
from ._setup import bot, config
from discord.ext import commands
from bot import converters

config = config['ticket']


@bot.group(name='ticket')
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    pass


# TODO: Rework/Rethink error system. (Throw exceptions)
@ticket.command(name='create')
@commands.guild_only()
async def _create(ctx, title: str, description: str=None, scope: converters.Scope=None):
    """ This is to create a support ticket. """

    t = Ticket()

    min_len = config['title']['min-len']
    max_len = config['title']['max-len']

    if len(title) > max_len:
        await ctx.send(f"Title too long: (max. `{max_len}` characters | `{len(title)}` given)\n"
                       f"Try to keep the title short and on-point. Use the description to get into detail.")

    elif len(title) < min_len:
        await ctx.send(f"Title too short: (min. `{min_len}` characters | `{len(title)}` given)")

    else:
        utc = time.time()

        t.title = title

        t.description = description

        t.state = "open"
        t.updated = utc

        author = merge_user(ctx.author)
        t.created_by.add(author, properties={'UTC': utc})

        guild = merge_guild(ctx.guild)
        t.located_on.add(guild)

        if scope is None:
            scope = t.guild.default_scope

        t.scope = scope

        highest_id = graph.run("MATCH (t: Ticket) RETURN max(t.id)").evaluate()
        if highest_id is None:
            highest_id = 0

        t.id = highest_id + 1

        graph.create(t)

        await ctx.send(f"Ticket created :white_check_mark: \n"
                       f"ID: `{t.id}`")

        await notify_supporters(ctx, "New ticket:", t)


@_create.error
async def _creation_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Tickets can't be created via DM.")

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
        await ctx.send("Given ticket is not located on this server.")
        return None

    elif t.scope == 'private':
        if t.guild.support_role not in [role.id for role in ctx.author.roles]:
            ctx.send("This ticket is private. :lock:")
            return None

    emb = ticket_embed(bot, t)

    await ctx.send(embed=emb)


@_show.error
async def _show_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Which ticket do you wanna see?:')

        def check(m):
            return m.author == ctx.author

        msg = await bot.wait_for('message', check=check)

        try:
            ticket_id = int(msg.content)
        except ValueError:
            ticket_id = msg.content

        await ctx.invoke(_show, ticket_id)

    elif isinstance(error, commands.BadArgument):
        await ctx.send(error)

    else:
        logger.error(error)


@ticket.command(name='close')
async def _close(ctx, t: converters.Ticket):  # TODO: add optional closing response
    """ This is to close a specific support ticket. """

    if is_author_or_supporter(ctx, t):
        if t.state == 'closed':
            await ctx.send("This ticket is already closed.")
            return None

        utc = time.time()

        t.state = 'closed'

        user = merge_user(ctx.author)
        t.closed_by.add(user, properties={'UTC': utc})

        t.updated = utc

        graph.push(t)

        await ctx.send("Ticket closed. :white_check_mark:")

        await notify_supporters(ctx, f"{ctx.author.mention} just closed ticket #{t.id}.", t, embed=False)

        # TODO: notify ticket author

    else:
        raise commands.MissingPermissions


@ticket.command(name='reopen')
async def _reopen(ctx, t: converters.Ticket):
    """ This is to reopen a specific support ticket. """

    if is_author_or_supporter(ctx, t):
        if t.state != 'closed':
            await ctx.send("This ticket is not closed.")
            return None

        utc = time.time()

        t.state = 'reopened'

        user = merge_user(ctx.author)
        t.reopened_by.add(user, properties={'UTC': utc})

        t.updated = utc

        graph.push(t)

        await ctx.send("Ticket reopened. :white_check_mark:")

        await notify_supporters(ctx, f"{ctx.author.mention} just reopened a ticket:", t)

    else:
        raise commands.MissingPermissions


@_close.error
@_reopen.error
async def _close_reopen_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You have to be supporter or the ticket author for this.")

    else:
        logger.error(error)
