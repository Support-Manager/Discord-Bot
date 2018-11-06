from bot.models import Guild


async def on_guild_join(guild):
    Guild.from_discord_guild(guild)
