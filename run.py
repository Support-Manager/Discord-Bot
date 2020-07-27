from bot import Bot, CONFIG, logger, dynamic_prefix
import logging
import sys
import os


logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logger.addHandler(console)


bot = Bot(
    command_prefix=dynamic_prefix,
    pm_help=None,
    case_insensitive=True,
    shard_count=int(os.getenv("SHARD_COUNT", "1")),
    shard_ids=list(map(int, os.getenv("SHARD_IDS", "0").split(","))),
    post_stats=os.getenv("POST_BOT_STATS") in ("1", "true")
)

bot.remove_command('help')


bot.load_extension('bot.event_handlers')
bot.load_extension('bot.commands')
bot.load_extension('bot.services')


bot.run(os.getenv('BOT_TOKEN'))
