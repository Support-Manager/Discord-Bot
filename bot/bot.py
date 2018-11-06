from discord.ext import commands
import logging
from ruamel import yaml
import os
from functools import wraps
from .context import Context


logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)

    with open(os.path.dirname(__file__) + '/translations/strings.yml', 'r', encoding='utf-8') as stream:
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

    @staticmethod
    def prime_feature(f: callable) -> callable:
        @wraps(f)
        async def wrapper(ctx, *args, **kwargs):
            if not ctx.is_prime():
                await ctx.send(ctx.translate("this is a prime feature"))
            else:
                await f(ctx, *args, *kwargs)

        return wrapper
