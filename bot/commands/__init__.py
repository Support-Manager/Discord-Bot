def setup(bot):
    from . import _setup
    _setup.bot = bot

    from .config import config
    from .ticket import ticket
    from .tickets import tickets
    from .response import response
    from .help import help_messages
