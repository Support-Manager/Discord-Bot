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
        server.default_confidence = default['confidence']

        graph.create(server)

    return server


def merge_user(user):
    u = User.select(graph, user.id).first()

    if u is None:
        u = User()

        u.uid = user.id

        graph.create(u)

    return u
