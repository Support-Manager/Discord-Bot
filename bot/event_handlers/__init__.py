from .on_ready import setup_ready_handler

from .before_invoke import before_invoke
from .on_guild_join import on_guild_join
from .on_member_join import on_member_join
from .on_command_error import on_command_error
from .on_error import on_error


def setup(bot):
    bot.add_listener(setup_ready_handler(bot))

    bot.before_invoke(before_invoke)
    bot.add_listener(on_guild_join)
    bot.add_listener(on_member_join)
    bot.add_listener(on_command_error)
    bot.add_listener(on_error)
