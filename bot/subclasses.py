from discord.ext import commands
from bot.utils import get_guild, logger
from ruamel import yaml


class Context(commands.Context):
    @property
    def db_guild(self):
        return get_guild(self.guild)

    @property
    def language(self):
        return self.db_guild.language

    def translate(self, text: str):
        return self.bot.string_translations[text][self.language]


class Bot(commands.Bot):
    with open('translations/strings.yml', 'r', encoding='utf-8') as stream:
        try:
            _string_translations = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            logger.error(exc)

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    @property
    def string_translations(self):
        return Bot._string_translations
