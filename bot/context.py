import discord
from discord.ext import commands
from .models import Guild, User, Ticket, Response
from .properties import CONFIG, Defaults
from typing import Union


class Context(commands.Context):
    @property
    def db_guild(self):
        return Guild.from_discord_guild(self.guild, ctx=self)

    @property
    def db_author(self):
        return User.from_discord_user(self.author, ctx=self)

    @property
    def language(self):
        return self.db_guild.language

    def translate(self, text: str):
        translations = self.bot.string_translations[text]

        return translations.get(self.language, translations[Defaults.LANGUAGE])

    def may_fully_access(self, ticket_or_response: Union[Ticket, Response]):
        if isinstance(ticket_or_response, Ticket):  # check if user is assigned to the ticket
            is_assigned = ticket_or_response.responsible_user == self.db_author
        else:
            is_assigned = False

        return ticket_or_response.guild.support_role in [role.id for role in self.author.roles] \
            or self.author.id == ticket_or_response.author.id \
            or self.author.permissions_in(self.channel).administrator \
            or self.author.id in CONFIG['bot_admins'] \
            or is_assigned

    def is_prime(self):
        discord_guild: discord.Guild = self.bot.get_guild(CONFIG['home_guild'])
        member = discord_guild.get_member(self.author.id)
        prime_roles = [discord_guild.get_role(r_id) for r_id in CONFIG['prime_roles']]

        if member is not None:
            return any(role in member.roles for role in prime_roles)  # checks if member has any prime role
        else:
            return False
