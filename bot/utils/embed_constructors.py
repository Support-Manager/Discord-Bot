import discord
import time
from bot import enums
from bot.properties import Defaults
from bot.models import Ticket, Response


def ticket_embed(ctx, t: Ticket):
    author = ctx.bot.get_user(t.author.id)

    emb = discord.Embed(
        title=t.title,
        description=t.description,
        color=Defaults.COLOR
    )

    t_id = t.id
    if t.scope_enum == enums.Scope.CHANNEL:
        t_channel = t.channel
        if t_channel is not None:
            t_id = t_channel.mention

    emb.add_field(
        name="ID",
        value=t_id
    )
    emb.add_field(
        name="Scope",
        value=t.scope
    )
    emb.add_field(
        name="State",
        value=t.state
    )

    if isinstance(ctx.channel, discord.DMChannel):  # only need to display guild in DM channels
        emb.add_field(
            name="Guild",
            value=t.guild.discord.name
        )

    if len(t.assigned_to) > 0:
        emb.add_field(
            name="Assigned to",
            value=f"`{t.responsible_user.discord}`"
        )

    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    creation_time = t.created_by.get(t.author, 'UTC')
    creation_gmtime = time.gmtime(creation_time)

    if creation_gmtime.tm_yday > time.gmtime().tm_yday or creation_gmtime.tm_year > time.gmtime().tm_year:
        emb.add_field(
            name=ctx.translate("created on"),
            value=time.strftime("%B %d, %Y", time.gmtime(creation_time))
        )

    if creation_time < t.updated:
        emb.set_footer(
            text=time.strftime(f"{ctx.translate('updated on')} %B %d, %Y at %I:%M %P UTC", time.gmtime(t.updated))
        )

    return emb


def response_embed(ctx, r: Response):
    author = ctx.bot.get_user(r.author.id)

    emb = discord.Embed(
        title=f"Re: {r.ticket.title}",
        description=r.content,
        color=Defaults.COLOR
    )
    emb.add_field(
        name="ID",
        value=r.full_id
    )
    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    creation_time = r.created_by.get(r.author, 'UTC')
    creation_gmtime = time.gmtime(creation_time)

    if creation_gmtime.tm_yday > time.gmtime().tm_yday or creation_gmtime.tm_year > time.gmtime().tm_year:
        emb.add_field(
            name="Created on",
            value=time.strftime("%B %d, %Y", time.gmtime(creation_time))
        )

    if creation_time < r.updated:
        emb.set_footer(
            text=time.strftime(f"{ctx.translate('updated on')} %B %d, %Y at %I:%M %P UTC", time.gmtime(r.updated))
        )

    return emb
