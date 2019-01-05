from discord.ext import commands
import logging
from ruamel import yaml
import os
from .context import Context
from .properties import CONFIG
import asyncio
import dbl


logger = logging.getLogger(__name__)


class Bot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)

        self.dbl = dbl.Client(bot=self, token=CONFIG['dbl_api_token'])
        self.loop.create_task(self._update_stats())

    with open(os.path.dirname(__file__) + '/translations/strings.yml', 'r', encoding='utf-8') as stream:
        try:
            _string_translations = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            logger.error(exc)

    async def _update_stats(self):
        """This function runs every 30 minutes to automatically update the server count."""

        await self.wait_until_ready()

        while not self.is_closed():
            logger.info('attempting to post server count')
            try:
                await self.dbl.post_server_count(shard_count=self.shard_count)
                logger.info('posted server count ({})'.format(len(self.guilds)))
            except Exception as e:
                logger.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))
            await asyncio.sleep(1800)

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    @property
    def string_translations(self):
        return Bot._string_translations
