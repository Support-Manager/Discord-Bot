import discord
from bot.utils import *
from discord.ext import commands
from bot.models import User, Ticket
from bot.properties import Defaults
from bot import enums
from copy import deepcopy


@commands.group()
@commands.guild_only()
async def tickets(ctx):
    if ctx.invoked_subcommand is None:
        user = None

        if ctx.subcommand_passed is not None:
            try:
                user = await User().convert(ctx, ctx.subcommand_passed)
            except commands.BadArgument:
                pass

        list_tickets = ctx.bot.get_command('tickets list')
        await ctx.invoke(list_tickets, user=user)


@tickets.command(name="list")
async def _list(ctx, user: User=None):
    """ Shows a list of tickets on the server/of a specific user. """

    guild = ctx.db_guild

    tickets_emb = discord.Embed(
        title=ctx.translate("active support tickets"),
        color=Defaults.COLOR
    )
    tickets_emb.set_footer(
        text=ctx.translate("to see all properties of a ticket use the ticket show command")
    )

    if user is not None:
        tickets_emb.description = ctx.translate("all open tickets of the given user")
        tickets_emb.set_author(
            name=f"{user.discord.name}#{user.discord.discriminator}",
            icon_url=user.discord.avatar_url
        )

        ticket_list = user.get_tickets()

    else:
        tickets_emb.description = ctx.translate("all open tickets of this guild")

        tickets_emb.set_author(
            name=guild.discord.name,
            icon_url=guild.discord.icon_url
        )

        ticket_list = guild.get_tickets()

    ticket_list = list(filter(lambda t: t.state_enum != enums.State.CLOSED, ticket_list))
    ticket_list.reverse()

    if not ctx.may_fully_access:
        def scope_check(t):
            c = t.scope_enum == enums.Scope.LOCAL or (t.scope_enum == enums.Scope.CHANNEL and ctx.channel == t.channel)
            return c

        ticket_list = list(filter(scope_check, ticket_list))  # check scope permissions

    if len(ticket_list) == 0:
        await ctx.send(ctx.translate("there are no active support tickets"))
        return None

    sub_lists = EmbedPaginator.generate_sub_lists(ticket_list)

    pages = []
    for sub_list in sub_lists:
        page = deepcopy(tickets_emb)  # copy by value not reference
        for ticket in sub_list:
            page.add_field(
                name=f"#{ticket.id} || {ticket.title}",
                value=ticket.description or "|",
                inline=False
            )
        pages.append(page)

    paginator = EmbedPaginator(ctx, pages)
    await paginator.run()


@tickets.command(name="close")
async def _close(ctx, *_tickets: Ticket):
    close_ticket = ctx.bot.get_command('ticket close')

    for t in _tickets:
        await ctx.invoke(close_ticket, t)


@tickets.error
async def tickets_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("tickets can't be accessed via dm"))
