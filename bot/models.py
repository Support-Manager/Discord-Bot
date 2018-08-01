from discord.ext import commands
import discord
from neo4j_connection import Graph, TicketMixin, ResponseMixin, GuildMixin, UserMixin
from py2neo.ogm import GraphObject
import logging
from .properties import Defaults, CONFIG
from . import enums
import re


logger = logging.getLogger(__name__)


graph = Graph(password=CONFIG['neo4j_password'])  # represents database connection


class Scope(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            scope = enums.Scope(argument)  # returns enum by value
        except ValueError:
            raise commands.BadArgument("Given scope doesn't exist.")

        return scope.value  # TODO: consider returning full enum


class Language(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            lang = enums.Language[argument.upper()]  # return enum by name
        except KeyError:
            raise commands.BadArgument("Given Language is not available.")

        return lang.value  # TODO: consider returning full enum


class Ticket(TicketMixin, commands.Converter):
    def __init__(self, ctx=None):
        self._creation_ctx = ctx
        super(Ticket, self).__init__()

    async def convert(self, ctx, argument):
        if type(argument) == str:
            if argument.startswith('#'):
                argument = argument[1:]
            else:
                try:
                    channel = await commands.TextChannelConverter().convert(ctx, argument)
                except commands.BadArgument:
                    channel = None

                if channel is not None:
                    argument = channel.name  # channel name == ticket id

        try:
            t = self.get(int(argument), ctx=ctx)
        except ValueError:
            t = None

        if t is None:
            raise commands.BadArgument("Given ticket can't be found.")
        else:
            return t

    @classmethod
    def get(cls, id: int, ctx=None):
        t = cls(ctx=ctx)
        t.id = id

        try:
            graph.pull(t)
        except TypeError:
            t = None

        return t

    @property
    def scope_enum(self):
        if self.scope is not None:
            return enums.Scope(self.scope)
        else:
            return None

    @property
    def state_enum(self):
        if self.state is not None:
            return enums.State(self.state)
        else:
            return None

    @property
    def guild(self):
        g = list(self.located_on)[0]

        if self._creation_ctx is not None:
            g = Guild.get(self._creation_ctx, g.id)

        return g

    @property
    def author(self):
        a = list(self.created_by)[0]

        if self._creation_ctx is not None:
            a = User.get(self._creation_ctx, a.id)

        return a

    @property
    def channel(self):
        return discord.utils.get(self.guild.discord.channels, name=str(self.id))


class Response(commands.Converter, ResponseMixin):
    async def convert(self, ctx, argument):
        try:
            r = self.select(graph, int(argument)).first()
        except ValueError:
            r = None

        if r is None:
            raise commands.BadArgument("Given response can't be found.")
        else:
            return r


class Guild(GuildMixin, commands.IDConverter):
    __primarylabel__ = "Guild"

    def __init__(self, discord_guild: discord.Guild=None):
        self._discord = discord_guild

        if self._discord is not None:
            self.id = discord_guild.id
        else:
            self.id = None

        super(Guild, self).__init__()

    async def convert(self, ctx, argument):
        result = None
        match = self._get_id_match(argument)  # uses RegEx defined in commands.IDConverter

        if match:
            guild_id = int(match.group(1))
            discord_guild = ctx.bot.get_guild(guild_id)
        else:
            discord_guild = None

        if discord_guild is not None:
            result = self.from_discord_guild(discord_guild)  # converts discord.Guild into this class

        if result is None:
            raise commands.BadArgument('Guild "{}" not found'.format(argument))
        else:
            return result

    @classmethod
    def from_discord_guild(cls, guild: discord.Guild):
        g = cls(guild)

        try:
            graph.pull(g)
        except TypeError:  # when guild is not in database yet
            g = cls(guild)  # re-initialize broken object
            g.id = guild.id
            g.prefix = Defaults.PREFIX
            g.default_scope = Defaults.SCOPE
            g.language = Defaults.LANGUAGE

            graph.create(g)
            logger.info(f"Added guild to database: {g.id}")

        return g

    @classmethod
    def get(cls, ctx, id: int):
        guild = ctx.bot.get_guild(id)
        return cls.from_discord_guild(guild)

    @property
    def language_enum(self):
        if self.language is not None:
            return enums.Language(self.language)
        else:
            return None

    @property
    def discord(self):
        return self._discord

    def push(self):
        graph.push(self)


class User(commands.Converter, UserMixin):
    def __init__(self, discord_user: discord.User=None):
        self._discord = discord_user

        if self._discord is not None:
            self.id = discord_user.id
        else:
            self.id = None

    async def convert(self, ctx, argument):
        result = None

        discord_user = await commands.UserConverter().convert(ctx, argument)
        if discord_user:
            result = self.from_discord_user(discord_user)  # converts discord.User into this class

        if result is None:
            raise commands.BadArgument('User "{}" not found'.format(argument))
        else:
            return result

    @classmethod
    def from_discord_user(cls, user: discord.User):
        u = cls(user)

        try:
            graph.pull(u)
        except TypeError:
            u = cls(user)  # re-initializing broken object
            u.id = user.id
            graph.create(u)
            logger.info(f"Added user to database: {u.id}")

        return u

    @classmethod
    def get(cls, ctx, id: int):
        discord_user = ctx.bot.get_user(id)
        return cls.from_discord_user(discord_user)

    @property
    def discord(self):
        return self._discord

    def push(self):
        graph.push(self)


class DiscordModelChild:
    def __init__(self, discord_model=None):
        if not issubclass(self.__class__, GraphObject):
            raise Exception("Derived classes need to derive from py2neo.ogm.GraphObject as well.")

        self._discord = discord_model

        if self._discord is not None:
            self.id = discord_model.id
        else:
            self.id = None

    async def convert(self, ctx, argument):
        result = None

        discord_model = await self._convert_discord_model(ctx, argument)

        if discord_model:
            result = self.from_discord_model(discord_model)  # converts discord.User into this class

        if result is None:
            raise commands.BadArgument('User "{}" not found'.format(argument))
        else:
            return result

    async def _convert_discord_model(self, ctx, argument):
        raise NotImplementedError('Derived classes need to implement this.')

    @classmethod
    def from_discord_model(cls, model):
        dmc = cls(model)

        try:
            dmc.pull()
        except AttributeError:
            dmc = cls(model)  # re-initializing broken object
            dmc.id = model.id
            dmc.pull_default_values()
            graph.create(dmc)
            logger.info(f"Added {cls.__name__} to database: {dmc.id}")

        return dmc

    def pull_default_values(self):
        raise NotImplementedError('Derived classes need to implement this.')

    def pull(self):
        graph.pull(self)

    @property
    def discord(self):
        return self._discord
