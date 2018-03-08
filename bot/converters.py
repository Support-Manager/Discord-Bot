from discord.ext import commands
from .utils import *


class Scope(commands.Converter):
    async def convert(self, ctx, argument):
        if argument in ["private", "local", "public"]:
            return argument

        else:
            raise commands.BadArgument("Given scope doesn't exist.")


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
