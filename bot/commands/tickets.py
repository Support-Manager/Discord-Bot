from bot.utils import *
from ._setup import bot


@bot.command(aliases=['list', 'all'])
async def tickets(ctx, user: discord.User=None):
    """ Shows a list of tickets on the server/of a specific user. """

    tickets_emb = discord.Embed(
        title="Active support tickets",
        color=embed_color
    )

    if user is not None:
        tickets_emb.description = "All open tickets of the given user."
        tickets_emb.set_author(
            name=f"{user.name}#{user.discriminator}",
            icon_url=user.avatar_url
        )

        db_user = User.select(graph, user.id).first()

        ticket_list = list(db_user.tickets)

    else:
        tickets_emb.description = "All open tickets of this guild."

        guild = Guild.select(graph, ctx.guild.id).first()

        ticket_list = list(guild.tickets)

    # TODO: check scopes
    ticket_list = list(filter(lambda t: t.state != 'closed', ticket_list))
    ticket_list.reverse()

    if len(ticket_list) == 0:
        await ctx.send("There are no active support tickets.")
        return None

    for ticket in ticket_list:
        tickets_emb.add_field(
            name=f"#{ticket.id} || {ticket.title}",
            value=ticket.description,
            inline=False
        )

    tickets_emb.set_footer(
        text="To see all properties of a ticket use the 'ticket show' command."
    )

    await ctx.send(embed=tickets_emb)
