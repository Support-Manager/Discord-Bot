from discord.ext import commands
from .models import Guild, User, Ticket, Response
from .properties import CONFIG, Defaults
from typing import Union


class Context(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

        self._cache = dict()

    @property
    async def db_guild(self):
        if self._cache.get('db_guild') is None:
            self._cache['db_guild'] = await Guild.async_from_discord_guild(self.guild, ctx=self)

        return self._cache['db_guild']

    @property
    async def db_author(self):
        if self._cache.get('db_author') is None:
            self._cache['db_author'] = await User.async_from_discord_user(self.author, ctx=self)

        return self._cache['db_author']

    @property
    def language(self):
        if self._cache.get('db_guild') is None:
            self._cache['db_guild'] = Guild.from_discord_guild(self.guild, ctx=self)

        return self._cache['db_guild'].language

    def translate(self, text: str):
        translations = self.bot.string_translations[text]

        return translations.get(self.language, translations[Defaults.LANGUAGE])

    async def may_fully_access(self, ticket_or_response: Union[Ticket, Response]):
        if isinstance(ticket_or_response, Ticket):  # check if user is assigned to the ticket
            is_assigned = ticket_or_response.responsible_user == await self.db_author
        else:
            is_assigned = False

        return ticket_or_response.guild.support_role in [role.id for role in self.author.roles] \
            or self.author.id == ticket_or_response.author.id \
            or self.author.permissions_in(self.channel).administrator \
            or self.author.id in CONFIG['bot_admins'] \
            or is_assigned

    async def is_prime(self):
        return (await self.db_author).prime
