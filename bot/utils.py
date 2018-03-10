import discord
from neo4j_connection import *
import json
import logging
import sys
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logger.addHandler(console)

with open('secrets.json', 'r', encoding='utf-8') as s:
    secrets = json.load(s)

graph = Graph(password=secrets['neo4j'])

with open('default.json', 'r', encoding='utf-8') as d:
    default = json.load(d)

EMBED_COLOR = 0x37ceb2


async def dynamic_prefix(bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return default['prefix']

    guild = Guild()
    guild.id = msg.guild.id
    graph.pull(guild)

    return guild.prefix


def merge_guild(guild):
    g = Guild.select(graph, guild.id).first()

    if g is None:
        g = Guild()

        g.id = guild.id
        g.prefix = default['prefix']
        g.default_scope = default['scope']

        graph.create(g)

    return g


def merge_user(user):
    u = User.select(graph, user.id).first()

    if u is None:
        u = User()

        u.id = user.id

        graph.create(u)

    return u


def ticket_embed(bot, t: Ticket):
    author = bot.get_user(t.author.id)
    guild = bot.get_guild(t.guild.id)

    emb = discord.Embed(
        title=t.title,
        description=t.description,
        color=EMBED_COLOR
    )
    emb.add_field(
        name="ID",
        value=t.id
    )
    emb.add_field(
        name="Guild",
        value=guild
    )
    emb.add_field(
        name="Scope",
        value=t.scope
    )
    emb.add_field(
        name="State",
        value=t.state
    )
    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    creation_time = t.created_by.get(t.author, 'UTC')
    creation_gmtime = time.gmtime(creation_time)

    if creation_gmtime.tm_yday > time.gmtime().tm_yday or creation_gmtime.tm_year > time.gmtime().tm_year:
        emb.add_field(
            name="Created on",
            value=time.strftime("%B %d, %Y", time.gmtime(creation_time))
        )

    if creation_time < t.updated:
        emb.set_footer(
            text=time.strftime("Updated on %B %d, %Y at %I:%M %P UTC", time.gmtime(t.updated))
        )

    return emb


async def notify_supporters(ctx, message, ticket: Ticket, embed=True):
    guild = ticket.guild

    channel_id = guild.channel
    if channel_id is not None and ticket.scope != 'public':
        channel = ctx.bot.get_channel(channel_id)

        mention = ""

        if guild.support_role is not None:
            role = discord.utils.find(lambda r: r.id == guild.support_role, ctx.guild.roles)
            if role is not None:
                mention = role.mention

        if embed:
            await channel.send(f"{message} {mention}", embed=ticket_embed(ctx.bot, ticket))
        else:
            await channel.send(f"{message} {mention}")


def is_author_or_supporter(ctx, ticket: Ticket):
    return ticket.guild.support_role in [role.id for role in ctx.author.roles] or ctx.author.id == ticket.author.id