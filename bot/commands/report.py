from discord.ext import commands
import discord
from bot.models import User, ReportMixin, graph
import time
from bot.utils import escaped, notify_supporters
import uuid


@commands.command()
async def report(ctx, user: User, reason: str):
    db_author: User = ctx.db_author

    if user in [r.affected_user for r in db_author.issued_reports]:
        await ctx.send(ctx.translate("you already reported this user"))
    elif db_author.id == user.id:
        await ctx.send(ctx.translate("you cannot report yourself"))
        return

    else:
        db_guild = ctx.db_guild

        report_node = ReportMixin()
        report_node.reason = escaped(reason)
        report_node.utc = time.time()
        report_node.uuid = uuid.uuid4().hex
        report_node.issued_on.add(db_guild)
        report_node.issued_by.add(db_author)
        report_node.applies_to.add(user)

        graph.create(report_node)

        await ctx.send(ctx.translate("user reported"))

        if len(user.reports) == 3:
            msg_addition = ctx.translate("user has been reported three times now")
        else:
            msg_addition = ""

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
