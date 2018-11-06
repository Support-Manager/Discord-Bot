import discord
from bot import bot
from bot.models import User
import time
from bot.utils import escaped, notify_supporters


@bot.command()
async def report(ctx, user: User, reason: str):
    db_author: User = ctx.db_author

    if user in db_author.has_reported:
        await ctx.send(ctx.translate("you already reported this user"))
    elif db_author.id == user.id:
        await ctx.send(ctx.translate("you cannot report yourself"))
        return

    else:
        user.reported_by.add(db_author, properties={'utc': time.time(), 'reason': escaped(reason)})
        user.push()

        await ctx.send(ctx.translate("user reported"))

        if len(user.reported_by) == 3:
            msg_addition = ctx.translate("user has been reported three times now")
        else:
            msg_addition = ""

        db_guild = ctx.db_guild

        await notify_supporters(
            ctx.bot,
            ctx.translate("[user] reported [user] because of [reason]"
                          ).format(ctx.author, user.discord, escaped(reason)
                                   ) + msg_addition,
            db_guild
        )

        await db_guild.log(
            ctx.translate("[user] has been reported because of [reason]").format(user.discord, escaped(reason))
        )

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
