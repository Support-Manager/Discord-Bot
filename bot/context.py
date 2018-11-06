from discord.ext import commands
from .models import Guild, User, Ticket, Response
from .properties import CONFIG


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
        return self.bot.string_translations[text][self.language]

    def may_fully_access(self, entry: Ticket or Response):
        return entry.guild.support_role in [role.id for role in self.author.roles] \
               or self.author.id == entry.author.id \
               or self.author.permissions_in(self.channel).administrator \
               or self.author.id in CONFIG['bot_admins']

    def is_prime(self):
        member = self.author
        discord_guild = self.bot.get_guild(CONFIG['home_guild'])
        prime_roles = [discord_guild.get_role(r_id) for r_id in CONFIG['prime_roles']]

        if member in discord_guild.members:
            return any(role in member.roles for role in prime_roles)  # checks if member has any prime role
        else:
            return False
