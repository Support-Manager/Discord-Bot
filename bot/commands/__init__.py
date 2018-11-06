from .config import config
from .ticket import ticket
from .tickets import tickets
from .response import response
from .help import help_messages
from .outlaw import outlaw
from .statistics import statistics
from .blacklist import blacklist
from .report import report


def setup(bot):
    bot.add_command(config)
    bot.add_command(ticket)
    bot.add_command(tickets)
    bot.add_command(response)
    bot.add_command(help_messages)
    bot.add_command(outlaw)
    bot.add_command(statistics)
    bot.add_command(blacklist)
    bot.add_command(report)
