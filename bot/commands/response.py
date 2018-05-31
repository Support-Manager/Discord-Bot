from bot.utils import *
from ._setup import bot
from bot import converters


@bot.group()
async def response(ctx):
    """ Allows to perform different actions with a response. """

    pass


@response.command(name="create")
async def _create(ctx, ticket: converters.Ticket, content):
    """ This is to create new responses/to answer tickets. """

    if ticket.scope != 'public' and ctx.guild.id != ticket.guild.id:
        await ctx.send(ctx.translate("this is a local ticket of another guild"))
        return None

    elif ticket.scope == 'private' and not is_author_or_supporter(ctx, ticket):
        await ctx.send(ctx.translate("this is a private ticket"))
        return None

    elif ticket.state == 'closed':
        await ctx.send(ctx.translate("this ticket is closed"))
        return None

    utc = time.time()
    
    resp = Response()
    
    author = get_user(ctx.author)
    resp.created_by.add(author, properties={'UTC': utc})
    
    guild = get_guild(ctx.guild)
    resp.located_on.add(guild)
    
    resp.refers_to.add(ticket)

    resp.content = escaped(content)

    highest_id = graph.run("MATCH (r: Response) RETURN max(r.id)").evaluate()
    if highest_id is None:
        highest_id = 0

    resp.id = highest_id + 1

    graph.create(resp)

    await ctx.send(ctx.translate("response created").format(resp.id))

    resp_msg = ctx.translate("[user] just responded to your ticket [ticket]")

    await notify_author(ctx, resp_msg, ticket, embed=response_embed(ctx, resp))


@response.command(name="show")
async def _show(ctx, resp: converters.Response):
    """ This is to show a specific response. """

    ticket = resp.ticket

    if ticket.scope != 'public' and ctx.guild.id != ticket.guild.id:
        await ctx.send(ctx.translate("the related ticket is local of another guild"))
        return None

    elif ticket.scope == 'private' and not is_author_or_supporter(ctx, ticket):
        await ctx.send(ctx.translate("the related ticket is private"))
        return None

    emb = response_embed(ctx, resp)

    await ctx.send(embed=emb)
