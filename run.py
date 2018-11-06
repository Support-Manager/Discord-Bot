from bot import Bot, CONFIG, logger, dynamic_prefix
import logging
import sys


logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logger.addHandler(console)


bot = Bot(command_prefix=dynamic_prefix, pm_help=None, case_insensitive=True)

bot.remove_command('help')


bot.load_extension('bot.event_handlers')
bot.load_extension('bot.commands')
bot.load_extension('bot.services')


bot.run(CONFIG['bot_token'])
