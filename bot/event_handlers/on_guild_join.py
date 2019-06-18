from bot.models import Guild


async def on_guild_join(guild):
    await Guild.async_from_discord_guild(guild)
