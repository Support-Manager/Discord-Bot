from bot.utils import *
from ._setup import bot, config

config = config['ticket']


@bot.group(name='ticket')
async def ticket(ctx):
    """ Allows to perform different actions with a ticket. """

    pass


# TODO: Rework/Rethink error system. (Throw exceptions)
@ticket.command(name='create')
async def _create(ctx, title: str, description: str=None, scope: str=default['scope']):
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

        if scope in config['scopes']:
            t.scope = scope
        else:
            await ctx.send("Given scope doesn't exist.")

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
        if channel_id is not None and scope != 'public':
            channel = bot.get_channel(channel_id)

            await channel.send("New ticket:", embed=ticket_embed(bot, t))


@ticket.command(name="show")
async def _show(ctx, tid: int):
    t = Ticket.select(graph, tid).first()

    if t is None:
        await ctx.send("Given ticket can't be found.")
        return None

    elif t.closed:
        await ctx.send("This ticket is closed.")
        return None

    # TODO: check scope (permissions)

    emb = ticket_embed(bot, t)

    await ctx.send(embed=emb)
