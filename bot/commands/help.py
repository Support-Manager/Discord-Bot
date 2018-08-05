from bot.utils import *
from ._setup import bot
from discord.ext import commands
from ruamel import yaml
from bot.models import Guild
from bot.properties import Defaults, CONFIG
import os


with open(os.path.dirname(__file__) + '/../translations/help.yml', 'r', encoding='utf-8') as stream:
    try:
        help_translations = yaml.load(stream, Loader=yaml.Loader)  # TODO: complete help texts
    except yaml.YAMLError as exc:
        print(exc)


@bot.command(name='help')
async def help_messages(ctx, command: str=None):
    guild = Guild.from_discord_guild(ctx.guild)
    language = guild.language

    if command is None:
        help_embed = discord.Embed(
            title=ctx.translate("commands"),
            url=CONFIG['commands_url'],
            description=ctx.translate("an overview of all features of the bot"),
            color=Defaults.COLOR
        )

        help_embed.set_thumbnail(url=bot.user.avatar_url)

        for command in help_translations:
            help_embed.add_field(
                name=command,
                value=help_translations[command][language].format(prefix=ctx.prefix)
            )

        if ctx.author.guild_permissions.administrator:
            await ctx.send(embed=help_embed)
        else:
            help_embed.set_footer(text=ctx.translate("requested on [guild]").format(ctx.guild.name))

            await ctx.author.send(embed=help_embed)
            await ctx.send(ctx.translate("help sent via dm"))

    else:
        valid_command = False

        for cmd in bot.commands:
            if command == cmd.name or command in cmd.aliases:
                command = cmd.name
                valid_command = True

        if valid_command:
            help_embed = discord.Embed(
                title=command,
                url=CONFIG["commands_url"] + f"#{command}",
                description=help_translations[command][language].format(prefix=ctx.prefix),
                color=Defaults.COLOR
            )

            await ctx.send(embed=help_embed)

        else:
            await ctx.send(ctx.translate("command not found"))


@help_messages.error
async def help_messages_error(ctx, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send(ctx.translate("please enable receiving dms and try again"))
