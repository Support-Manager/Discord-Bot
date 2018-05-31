from discord.ext import commands
from .utils import *


class Scope(commands.Converter):
    async def convert(self, ctx, argument):
        if argument in CONFIG["scopes"]:
            return argument

        else:
            raise commands.BadArgument("Given scope doesn't exist.")


class Language(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.upper() in CONFIG["languages"]:
            return argument

        else:
            raise commands.BadArgument("Given Language is not available.")


class Ticket(commands.Converter, Ticket):
    async def convert(self, ctx, argument):
        try:
            t = Ticket.select(graph, int(argument)).first()
        except ValueError:
            t = None

        if t is None:
            raise commands.BadArgument("Given ticket can't be found.")
        else:
            return t


class Response(commands.Converter, Response):
    async def convert(self, ctx, argument):
        try:
            r = Response.select(graph, int(argument)).first()
        except ValueError:
            r = None

        if r is None:
            raise commands.BadArgument("Given response can't be found.")
        else:
            return r
