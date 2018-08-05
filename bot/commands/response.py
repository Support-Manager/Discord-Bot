from bot.utils import notify_author, escaped, response_embed
from ._setup import bot
from bot.models import graph, Ticket, User, Guild, Response
from bot import enums
import time
from discord.ext import commands


@bot.group()
@commands.guild_only()
async def response(ctx):
    """ Allows to perform different actions with a response. """

    pass


@response.error
async def response_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("responses can't be accessed via dm"))


@response.command(name="create")
async def _create(ctx, t: Ticket, content: str):
    """ This is to create new responses/to answer tickets. """

    if t.scope_enum == enums.Scope.CHANNEL and ctx.channel != t.channel and not ctx.may_fully_access(t):
        await ctx.send(ctx.translate("the related ticket is channel scope"))
        return None

    elif t.scope_enum == enums.Scope.PRIVATE and not ctx.may_fully_access(t):
        await ctx.send(ctx.translate("this is a private ticket"))
        return None

    elif t.state_enum == enums.State.CLOSED:
        await ctx.send(ctx.translate("this ticket is closed"))
        return None

    utc = time.time()
    
    resp = Response()
    
    author = User.from_discord_user(ctx.author)
    resp.created_by.add(author, properties={'UTC': utc})
    
    guild = Guild.from_discord_guild(ctx.guild)
    resp.located_on.add(guild)
    
    resp.refers_to.add(t)

    resp.content = escaped(content)

    resp.deleted = False

    highest_id = graph.run("MATCH (r: Response) RETURN max(r.id)").evaluate()
    if highest_id is None:
        highest_id = 0

    resp.id = highest_id + 1

    graph.create(resp)

    await ctx.send(ctx.translate("response created").format(resp.id))

    resp_msg = ctx.translate(
        "[user] just responded to your ticket [ticket]"
    ).format(ctx.author.name, ctx.author.discriminator, t.id)

    await notify_author(ctx, resp_msg, t, embed=response_embed(ctx, resp))


@response.command(name="show")
async def _show(ctx, resp: Response):
    """ This is to show a specific response. """

    t = resp.ticket

    if t.scope_enum == enums.Scope.CHANNEL and ctx.channel != t.channel and not ctx.may_fully_access(t):
        await ctx.send(ctx.translate("the related ticket is channel scope"))
        return None

    elif t.scope_enum == enums.Scope.PRIVATE and not ctx.may_fully_access(t):
        await ctx.send(ctx.translate("the related ticket is private"))
        return None

    emb = response_embed(ctx, resp)

    await ctx.send(embed=emb)


@response.command(name="delete")
async def _delete(ctx, resp: Response):
    """ This is to delete a response. """

    utc = time.time()
    ticket = resp.ticket

    if not (ctx.author.id == resp.author.id or ctx.may_fully_access(ticket)):
        await ctx.send(ctx.translate("you are not allowed to perform this action"))
        return None

    resp.deleted = True
    resp.deleted_by.add(User.from_discord_user(ctx.author), properties={'UTC': utc})

    resp.push()

    await ctx.send(ctx.translate("response deleted"))
