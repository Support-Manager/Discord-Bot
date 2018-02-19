from discord.ext import commands
from bot.utils import *
from ._setup import bot, config

config = config['config']


@bot.group(name='config', aliases=['set', 'configure'])
@commands.has_permissions(administrator=True)
async def configure(ctx):
    """ This is for admins to configure the bot's behaviour on their server. """

    if ctx.invoked_subcommand is None:
        await ctx.send("What would you like to configure?")


@configure.command(name='prefix')
async def _prefix(ctx, pfx: str = ""):
    """ This is to change the server's cmd prefix. """

    min_len = config['prefix']['min-len']
    max_len = config['prefix']['max-len']

    if len(pfx) > max_len:
        await ctx.send(f"Prefix can't be longer than {max_len} characters.")

    elif len(pfx) < min_len:
        await ctx.send(f"Prefix must be at least {min_len} character.")

    else:
        server = Server()
        server.sid = ctx.guild.id
        graph.pull(server)
        server.prefix = pfx
        graph.push(server)

        await ctx.send(f"Okay, your new prefix is: `{pfx}`.")


@configure.command(name='channel')
async def _channel(ctx, channel: discord.TextChannel):
    """ This is to set the server's support channel. """

    server = Server()
    server.sid = ctx.guild.id
    server.channel = channel.id
    graph.merge(server)

    await ctx.send(f"Okay, I'll send ticket events in {channel.mention} :white_check_mark:")
