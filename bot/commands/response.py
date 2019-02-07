from bot.utils import notify_author, escaped, response_embed
from bot.models import graph, Ticket, User, Response
from bot import enums, checks
import time
from discord.ext import commands
import discord
import uuid


@commands.group()
@commands.guild_only()
@checks.check_blacklisted()
async def response(ctx):
    """ Allows to perform different actions with a response. """

    pass


@response.error
async def response_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(ctx.translate("responses can't be accessed via dm"))


@response.command(name="create", aliases=["add"])
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

    if t.scope_enum == enums.Scope.PRIVATE:
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    utc = time.time()
    
    resp = Response()
    
    author = User.from_discord_user(ctx.author)
    resp.created_by.add(author, properties={'UTC': utc})

    resp.located_on.add(ctx.db_guild)
    
    resp.refers_to.add(t)

    resp.content = escaped(content)

    resp.deleted = False
    resp.updated = utc

    highest_id = graph.run(
        "MATCH (r:Response)-[:REFERS_TO]->(t:Ticket {uuid: '%s'}) RETURN max(r.id)" % t.uuid
    ).evaluate()
    if highest_id is None:
        highest_id = 0

    resp.id = highest_id + 1
    resp.uuid = uuid.uuid4().hex

    graph.create(resp)

    await ctx.send(ctx.translate("response created").format(resp.full_id))

    resp_msg = ctx.translate(
        "[user] just responded to your ticket [ticket]"
    ).format(ctx.author.name, ctx.author.discriminator, t.id)

    await notify_author(ctx, resp_msg, t, embed=response_embed(ctx, resp))
    await resp.guild.log(ctx.translate("[user] created response [response]").format(
        ctx.author, f"{resp.ticket.id}-{resp.id}"
    ))


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


@response.command(name="edit", aliases=["change", "update"])
async def _edit(ctx, resp: Response, content: str):
    """ This is to edit a specific response. """

    if resp.author.id != ctx.author.id:
        await ctx.send(ctx.translate("you are not allowed to perform this action"))

    else:
        resp.updated = time.time()

        resp.content = escaped(content)

        resp.push()

        await ctx.send(ctx.translate("response edited"))
        await resp.guild.log(ctx.translate("[user] edited response [response]").format(
            ctx.author, f"{resp.ticket.id}-{resp.id}"
        ))


@response.command(name="append", aliases=["addinfo"])
async def _append(ctx, resp: Response, content: str):
    new_content = f"{resp.content}\n{escaped(content)}"

    edit_cmd = ctx.bot.get_command("response edit")
    await ctx.invoke(edit_cmd, resp, new_content)


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
    await resp.guild.log(ctx.translate("[user] deleted response [response]").format(
        ctx.author, f"{resp.ticket.id}-{resp.id}"
    ))
