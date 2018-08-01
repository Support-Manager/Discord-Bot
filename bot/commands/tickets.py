from bot.utils import *
from ._setup import bot
from bot.models import User
from bot.properties import Defaults
from bot import enums


@bot.command(aliases=['list', 'all'])
async def tickets(ctx, user: User=None):
    """ Shows a list of tickets on the server/of a specific user. """

    guild = ctx.db_guild

    tickets_emb = discord.Embed(
        title=ctx.translate("active support tickets"),
        color=Defaults.COLOR
    )

    if user is not None:
        tickets_emb.description = ctx.translate("all open tickets of the given user")
        tickets_emb.set_author(
            name=f"{user.discord.name}#{user.discord.discriminator}",
            icon_url=user.discord.avatar_url
        )

        ticket_list = list(user.tickets)

    else:
        tickets_emb.description = ctx.translate("all open tickets of this guild")

        ticket_list = list(guild.tickets)

    ticket_list = list(filter(lambda t: t.state != 'closed', ticket_list))
    ticket_list.reverse()

    if not ctx.may_fully_access:
        def scope_check(t):
            c = t.scope_enum == enums.Scope.LOCAL or (t.scope_enum == enums.Scope.CHANNEL and ctx.channel == t.channel)
            return c

        ticket_list = list(filter(scope_check, ticket_list))  # check scope permissions

    if len(ticket_list) == 0:
        await ctx.send(ctx.translate("there are no active support tickets"))
        return None

    for ticket in ticket_list:
        tickets_emb.add_field(
            name=f"#{ticket.id} || {ticket.title}",
            value=ticket.description,
            inline=False
        )

    tickets_emb.set_footer(
        text=ctx.translate("to see all properties of a ticket use the ticket show command")
    )

    await ctx.send(embed=tickets_emb)
