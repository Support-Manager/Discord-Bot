from bot import utils, errors, Bot
from bot.models import Guild
import discord
import traceback
import sys


async def on_error(event, *args, **kwargs):
    exc_info = sys.exc_info()
    instance = exc_info[1]

    if event == "on_voice_state_update":
        member = args[0]
        guild = Guild.from_discord_guild(member.guild)

        translator = utils.Translator(Bot._string_translations, guild.language_enum)

        if isinstance(instance, errors.OnCooldown):
            seconds = int(instance.retry_after)
            try:
                await member.send(translator.translate("you're on cooldown for [sec] seconds").format(seconds))
            except discord.Forbidden:
                pass

        elif isinstance(instance, discord.Forbidden):
            await guild.log(translator.translate("not enough permissions to perform action"))

    else:
        print('Ignoring exception in {}'.format(event), file=sys.stderr)
        traceback.print_exc()
