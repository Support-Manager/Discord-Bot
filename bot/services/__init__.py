from .voice import setup_voice_state_update_handler


def setup(bot):
    listener = setup_voice_state_update_handler(bot)

    bot.add_listener(listener)
