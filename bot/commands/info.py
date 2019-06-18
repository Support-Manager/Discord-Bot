import discord
from discord.ext import commands
from bot import CONFIG, Defaults
from bot.models import graph


@commands.command(aliases=["about"])
async def info(ctx):
    info_emb = discord.Embed(
        title="Support-Manager",
        description=ctx.translate("about the bot"),
        color=Defaults.COLOR,
        url=CONFIG["bot_url"]
    )

    info_emb.set_author(
        name="Linus Bartsch | LiBa01#8817",
        url=CONFIG["imprint"],
        icon_url="https://avatars0.githubusercontent.com/u/30984789"  # GitHub avatar
    )

    info_emb.set_thumbnail(
        url=ctx.bot.user.avatar_url
    )

    info_emb.add_field(
        name=ctx.translate("developer"),
        value=f"{ctx.translate('name')}: **Linus Bartsch**\n"
              f"Discord: **LiBa01#8817**\n"
              f"GitHub: **[LiBa001](https://github.com/LiBa001)**\n"
              f"Patreon: **[LiBaSoft](https://www.patreon.com/user?u=8320690)**\n"
              f"{ctx.translate('I am also at')} **[discordbots.org](https://discordbots.org/user/269959141508775937)**",
        inline=False
    )

    info_emb.add_field(
        name=ctx.translate("used for development"),
        value=f"{ctx.translate('programming language')}: **[Python](https://python.org) 3.6**\n"
              f"Library: **discord.py** v1.0.0\n"
              f"{ctx.translate('database')}: **[Neo4j](https://neo4j.com) Community** v3.5.0  (library: py2neo v4.2.0)",
        inline=False
    )

    db_guild = await ctx.db_guild

    info_emb.add_field(
        name=ctx.translate("commands"),
        value=f"{ctx.translate('type [prefix]help for command overview').format(db_guild.prefix)}\n"
              f"{ctx.translate('for detailed info visit [url]').format(CONFIG['commands_url'])}",
        inline=False
    )

    info_emb.add_field(
        name=ctx.translate("some stats"),
        value=f"{ctx.translate('active users')}: **{graph.run('MATCH (u:User)<--() RETURN count(u)').evaluate()}**\n"
              f"{ctx.translate('total tickets')}: **{graph.run('MATCH (t:Ticket) RETURN count(t)').evaluate()}**\n"
              f"{ctx.translate('total responses')}: **{graph.run('MATCH (r:Response) RETURN count(r)').evaluate()}**",
        inline=False
    )

    info_emb.add_field(
        name="Sharding",
        value=f"{ctx.translate('shard count')}: **{ctx.bot.shard_count}**\n"
              f"{ctx.translate('this servers shard id')}: **{ctx.guild.shard_id}**",
        inline=False
    )

    await ctx.send(embed=info_emb)
