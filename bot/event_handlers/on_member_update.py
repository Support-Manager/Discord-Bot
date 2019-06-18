from bot.models import User
from bot.properties import CONFIG
from discord import Member
import logging


logger = logging.getLogger(__name__)


async def on_member_update(before: Member, after: Member):
    if before.guild.id != CONFIG['home_guild']:
        return

    prime_roles = CONFIG['prime_roles']

    was_prime = any(r.id in prime_roles for r in before.roles)
    is_prime = any(r.id in prime_roles for r in after.roles)

    if was_prime == is_prime:
        return  # abort because nothing has changed

    db_user = await User.async_from_discord_user(after)
    db_user.prime = is_prime  # update value
    await db_user.async_push()

    logger.info(f"{'added' if is_prime else 'removed'} prime member: {db_user.id}")
