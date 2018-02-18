from discord.ext import commands
from bot.utils import *
from ._setup import bot, config

config = config['ticket']


@bot.group(name='ticket')
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    pass


@ticket.command(name='create')
async def _create(ctx, title: str, description: str=None, confidence: str=default['confidence']):
    t = Ticket()

    min_len = config['title']['min-len']
    max_len = config['title']['max-len']

    if len(title) > max_len:
        await ctx.send(f"Title too long: (max. `{max_len}` characters | `{len(title)}` given)\n"
                       f"Try to keep the title short and on-point. Use the description to get into detail.")

    elif len(title) < min_len:
        await ctx.send(f"Title too short: (min. `{min_len}` characters | `{len(title)}` given)")

    else:
        t.title = title

        t.description = description
        t.confidence = confidence  # TODO: check confidence
        t.closed = False

        author = merge_user(ctx.author)
        t.created_by.add(author)

        server = merge_server(ctx.guild)
        t.created_on.add(server)

        highest_id = graph.run("MATCH (t: Ticket) RETURN max(t.id)").evaluate()
        if highest_id is None:
            highest_id = 0

        t.tid = highest_id + 1

        graph.create(t)

        await ctx.send(f"Ticket created :white_check_mark: \n"
                       f"ID: `{t.tid}`")

        channel_id = server.channel
        if channel_id is not None and confidence != 'public':
            channel = bot.get_channel(channel_id)

            await channel.send(f"{ctx.author.mention} just created a ticket.\n"
                               f"ID: `{t.tid}`")  # TODO: invoke "ticket show"
