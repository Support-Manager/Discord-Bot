import discord
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


def is_prime_only(command: commands.Command) -> bool:
    if 'prime_check' in [c.__name__ for c in command.checks]:
        return True
    else:
        return False


def get_translation(command_name: str, language: str):
    cmd_translations = help_translations[command_name]
    return cmd_translations.get(language, cmd_translations[Defaults.LANGUAGE])


@commands.command(name='help')
async def help_messages(ctx, command_name: str=None):
    guild = Guild.from_discord_guild(ctx.guild)
    language = guild.language

    footer_msg = f"*{ctx.translate('prime-feature')}; ¹{ctx.translate('optional')}"

    if command_name is None:
        help_embed = discord.Embed(
            title=ctx.translate("commands"),
            url=CONFIG['commands_url'],
            description=ctx.translate("an overview of all features of the bot").format(CONFIG['commands_url']),
            color=Defaults.COLOR
        )

        help_embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        for command_name in help_translations:
            command = ctx.bot.get_command(command_name)
            prime_only = is_prime_only(command)

            help_embed.add_field(
                name=command_name + ('*' if prime_only else ''),
                value=get_translation(command_name, language).format(prefix=ctx.prefix),
                inline=False
            )

        if not isinstance(ctx.author, discord.Member):
            help_embed.set_footer(text=footer_msg)

            await ctx.send

        elif ctx.author.guild_permissions.administrator:
            help_embed.set_footer(text=footer_msg)

            await ctx.send(embed=help_embed)
        else:
            help_embed.set_footer(text=f"{ctx.translate('requested on [guild]').format(ctx.guild.name)}; {footer_msg}")

            await ctx.author.send(embed=help_embed)
            await ctx.send(ctx.translate("help sent via dm"))

    else:
        valid_command = False

        for cmd in ctx.bot.commands:
            if command_name == cmd.name or command_name in cmd.aliases:
                command_name = cmd.name
                valid_command = True

        if valid_command:
            command = ctx.bot.get_command(command_name)
            prime_only = is_prime_only(command)

            help_embed = discord.Embed(
                title=command_name + ('*' if prime_only else ''),
                url=CONFIG["commands_url"] + f"#{command_name}",
                description=get_translation(command_name, language).format(prefix=ctx.prefix),
                color=Defaults.COLOR
            )
            help_embed.set_footer(text=footer_msg)

            await ctx.send(embed=help_embed)

        else:
            await ctx.send(ctx.translate("command not found"))


@help_messages.error
async def help_messages_error(ctx, error):
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send(ctx.translate("please enable receiving dms and try again"))
