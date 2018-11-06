from discord.ext import commands
import discord
from discord import Role as DiscordRole, Embed as DiscordEmbed
from neo4j_connection import Graph, TicketMixin, ResponseMixin, GuildMixin, UserMixin
from py2neo.ogm import GraphObject
import logging
from .properties import Defaults, CONFIG
from . import enums
import time


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
            t = self.get(int(argument), ctx.db_guild, ctx=ctx)
        except ValueError:
            t = None

        if t is None:
            raise commands.BadArgument("Given ticket can't be found.")
        else:
            return t

    @classmethod
    def get(cls, id: int, guild: GuildMixin, ctx=None):
        uuid = graph.run(
            "MATCH (t:Ticket {id: %i})-[:TICKET_LOCATED_ON]->(g:Guild {id: %i}) RETURN t.uuid" % (id, guild.id)
        ).evaluate()

        if uuid is not None:
            t = cls(ctx=ctx)
            t.uuid = uuid

            try:
                graph.pull(t)
            except TypeError:
                t = None
        else:
            t = None

        if t is not None:
            if t.state_enum == enums.State.DELETED:
                t = None

        return t

    @property
    def scope_enum(self):
        if self.scope is not None:
            return enums.Scope(self.scope)
        else:
            return None

    @scope_enum.setter
    def scope_enum(self, enum: enums.Scope):
        self.scope = enum.value

    @property
    def state_enum(self):
        if self.state is not None:
            return enums.State(self.state)
        else:
            return None

    @state_enum.setter
    def state_enum(self, enum: enums.State):
        self.state = enum.value

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

    def push(self):
        graph.push(self)

    def get_responses(self):
        responses = []
        for r in self.responses:
            response = Response.get(r.id, r.ticket, ctx=self._creation_ctx)
            if response is not None:
                responses.append(response)

        return responses


class Response(commands.Converter, ResponseMixin):
    def __init__(self, ctx=None):
        self._creation_ctx = ctx
        super().__init__()

    async def convert(self, ctx, argument):
        try:
            t_id, r_id = argument.split('-')
            t = Ticket.get(int(t_id), ctx.guild, ctx=ctx)
            r = self.get(int(r_id), t, ctx=ctx)
        except ValueError:
            r = None

        if r is None:
            raise commands.BadArgument("Given response can't be found.")
        else:
            return r

    @classmethod
    def get(cls, id: int, ticket: Ticket or TicketMixin, ctx=None):
        uuid = graph.run(
            "MATCH (r:Response {id: %i})-[:REFERS_TO]->(t:Ticket {uuid: '%s'}) RETURN r.uuid" % (id, ticket.uuid)
        ).evaluate()

        if uuid is not None:
            r = cls(ctx=ctx)
            r.uuid = uuid

            try:
                graph.pull(r)
            except TypeError:
                r = None
        else:
            r = None

        if r is not None:
            if r.deleted:
                r = None

        return r

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
    def ticket(self):
        t = list(self.refers_to)[0]

        if self._creation_ctx is not None:
            t = Ticket.get(t.id, t.guild, ctx=self._creation_ctx)

        return t

    def push(self):
        graph.push(self)

    @property
    def full_id(self):
        return f"{self.ticket.id}-{self.id}"


class Guild(GuildMixin, commands.IDConverter):
    __primarylabel__ = "Guild"

    def __init__(self, discord_guild: discord.Guild=None, ctx=None):
        self._discord = discord_guild

        if self._discord is not None:
            self.id = discord_guild.id
        else:
            self.id = None

        self._creation_ctx = ctx

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
            result = self.from_discord_guild(discord_guild, ctx=ctx)  # converts discord.Guild into this class

        if result is None:
            raise commands.BadArgument('Guild "{}" not found'.format(argument))
        else:
            return result

    @classmethod
    def from_discord_guild(cls, guild: discord.Guild, ctx=None):
        g = cls(guild, ctx=ctx)

        try:
            graph.pull(g)
        except TypeError:  # when guild is not in database yet
            g = cls(guild, ctx=ctx)  # re-initialize broken object
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
        return cls.from_discord_guild(guild, ctx=ctx)

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

    def get_tickets(self):
        tickets = []
        for t in self.tickets:
            ticket = Ticket.get(t.id, t.guild, ctx=self._creation_ctx)
            if ticket is not None:
                tickets.append(ticket)

        return tickets

    def get_responses(self):
        responses = []
        for r in self.responses:
            response = Response.get(r.id, r.ticket, ctx=self._creation_ctx)
            if response is not None:
                responses.append(response)

        return responses

    def get_support_role(self) -> DiscordRole:
        if self.support_role is not None:
            role = discord.utils.find(lambda r: r.id == self.support_role, self.discord.roles)

            return role

    async def log(self, message: str=None, *, embed: DiscordEmbed=None):
        if self.log_channel is not None:
            channel = self.discord.get_channel(self.log_channel)
            await channel.send(message, embed=embed)

    @property
    def updated_blacklist(self):
        bl = self.blacklist

        for user in bl:
            utc = bl.get(user, 'UTC')
            days = bl.get(user, 'days')

            if days is None:
                continue

            if utc + days * (60 * 60 * 24) > time.time():
                self.blacklist.remove(user)

        self.push()
        return bl


class User(commands.Converter, UserMixin):
    def __init__(self, discord_user: discord.User=None, ctx=None):
        self._discord = discord_user

        if self._discord is not None:
            self.id = discord_user.id
        else:
            self.id = None

        self._creation_ctx = ctx

        super().__init__()

    async def convert(self, ctx, argument):
        result = None

        discord_user = await commands.UserConverter().convert(ctx, argument)
        if discord_user:
            result = self.from_discord_user(discord_user, ctx=ctx)  # converts discord.User into this class

        if result is None:
            raise commands.BadArgument('User "{}" not found'.format(argument))
        else:
            return result

    @classmethod
    def from_discord_user(cls, user: discord.User, ctx=None):
        u = cls(user, ctx=ctx)

        try:
            graph.pull(u)
        except TypeError:
            u = cls(user, ctx=ctx)  # re-initializing broken object
            u.id = user.id
            graph.create(u)
            logger.info(f"Added user to database: {u.id}")

        return u

    @classmethod
    def get(cls, ctx, id: int):
        discord_user = ctx.bot.get_user(id)
        return cls.from_discord_user(discord_user, ctx=ctx)

    @property
    def discord(self):
        return self._discord

    def push(self):
        graph.push(self)

    def get_tickets(self):
        tickets = []
        for t in self.tickets:
            ticket = Ticket.get(t.id, t.guild, ctx=self._creation_ctx)
            if ticket is not None:
                tickets.append(ticket)

        return tickets

    def get_responses(self):
        responses = []
        for r in self.responses:
            response = Response.get(r.id, r.ticket, ctx=self._creation_ctx)
            if response is not None:
                responses.append(response)

        return responses


class DiscordModelChild:  # TODO: implement as Abstract Base Class for User and Guild (at least consider doing so)
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
