import discord
from neo4j_connection import *
import json
import logging
import sys

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

embed_color = 0x37ceb2


async def dynamic_prefix(bot, msg):
    server = Server()
    server.sid = msg.guild.id
    graph.pull(server)

    return server.prefix


def merge_server(guild):
    server = Server.select(graph, guild.id).first()

    if server is None:
        server = Server()

        server.sid = guild.id
        server.prefix = default['prefix']
        server.default_scope = default['scope']

        graph.create(server)

    return server


def merge_user(user):
    u = User.select(graph, user.id).first()

    if u is None:
        u = User()

        u.uid = user.id

        graph.create(u)

    return u


def ticket_embed(bot, t: Ticket):
    author = bot.get_user(t.author.uid)
    server = bot.get_guild(t.server.sid)

    emb = discord.Embed(
        title=t.title,
        description=t.description,
        color=embed_color
    )
    emb.add_field(
        name="ID",
        value=t.tid
    )
    emb.add_field(
        name="Server",
        value=server
    )
    emb.add_field(
        name="Scope",
        value=t.scope
    )
    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    return emb
