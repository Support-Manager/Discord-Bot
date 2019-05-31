from bot.models import Guild, User
import time


async def on_member_join(member):
    db_guild = await Guild.async_from_discord_guild(member.guild)
    db_user = await User.async_from_discord_user(member)

    db_guild.joined_users.add(db_user, properties={'UTC': time.time()})

    await db_guild.async_push()
