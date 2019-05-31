import discord
from bot.models import Guild, Ticket
from .embed_constructors import ticket_embed


async def notify_supporters(bot, message, db_guild: Guild, embed: discord.Embed=None, *, mention_supporters: bool=True):
    channel_id = db_guild.channel
    if channel_id is not None:
        channel = bot.get_channel(channel_id)

        mention = ""

        if mention_supporters:
            role = db_guild.get_support_role()
            if role is not None:
                mention = role.mention

        if embed is not None:
            await channel.send(f"{message} {mention}", embed=embed)
        else:
            await channel.send(f"{message} {mention}")


async def notify_ticket_authority(ctx, ticket: Ticket, message: str, *,
                                  send_embed: bool=False, suppress_mention: bool=False):
    """ Takes advanced care of the right notification for a ticket. """

    if send_embed:
        embed = ticket_embed(ctx, ticket)
    else:
        embed = None

    responsible_user = ticket.responsible_user
    if responsible_user is not None:
        if responsible_user == await ctx.db_author:
            return  # don't need to notify the user about what he did by his self

        channel_id = ticket.guild.channel
        if channel_id is not None:
            channel: discord.TextChannel = ctx.bot.get_channel(channel_id)

            if responsible_user.discord in channel.members:
                await channel.send(f"{responsible_user.discord.mention if not suppress_mention else ''}\n{message}")
                return

        else:
            channel = None

        try:
            await responsible_user.discord.send(message)
        except discord.Forbidden:
            if channel is not None:
                failed_contact = ctx.translate('failed to contact responsible user [user] for ticket [ticket]').format(
                    responsible_user.discord, ticket.id)

                await channel.send(f"{failed_contact}\n\n{message}")

    else:
        await notify_supporters(ctx.bot, message, ticket.guild, embed, mention_supporters=not suppress_mention)


async def notify_author(ctx, message, ticket: Ticket, embed=None):
    """ This is to notify a ticket author on specific events. """

    # It's not necessary to inform the author when the action was triggered by himself.
    if not ctx.author.id == ticket.author.id:
        try:
            member = ctx.guild.get_member(ticket.author.id)
            await member.send(message, embed=embed)
            return 0

        except discord.Forbidden:  # if a user has DMs disabled
            return 1
