from bot.models import Guild, User
import time


async def on_member_join(member):
    db_guild = Guild.from_discord_guild(member.guild)
    db_user = User.from_discord_user(member)

    db_guild.joined_users.add(db_user, properties={'UTC': time.time()})

    db_guild.push()
