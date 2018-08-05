import logging
import sys
import os
import discord
from discord.ext import commands
from ruamel import yaml
from .models import Guild, User, graph, Ticket, Response
from .properties import CONFIG, Defaults
from inspect import Parameter


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logger.addHandler(console)


class Context(commands.Context):
    @property
    def db_guild(self):
        return Guild.from_discord_guild(self.guild, ctx=self)

    @property
    def language(self):
        return self.db_guild.language

    def translate(self, text: str):
        return self.bot.string_translations[text][self.language]

    def may_fully_access(self, entry: Ticket or Response):
        return entry.guild.support_role in [role.id for role in self.author.roles] \
               or self.author.id == entry.author.id \
               or self.author.permissions_in(self.channel).administrator \
               or self.author.id in CONFIG['bot_admins']


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)

    with open(os.path.dirname(__file__) + '/translations/strings.yml', 'r', encoding='utf-8') as stream:
        try:
            _string_translations = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            logger.error(exc)

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    @property
    def string_translations(self):
        return Bot._string_translations


async def dynamic_prefix(bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return Defaults.PREFIX

    guild = Guild.from_discord_guild(msg.guild)

    return guild.prefix


bot = Bot(command_prefix=dynamic_prefix, pm_help=None, case_insensitive=True)

bot.remove_command('help')


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name}")

    for guild in bot.guilds:
        Guild.from_discord_guild(guild)

    await bot.change_presence(activity=discord.Game(name="/help"))


@bot.event
async def on_guild_join(guild):
    Guild.from_discord_guild(guild)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.BadArgument):
        cmd: commands.Command = ctx.command

        successful_parsed_args = len(ctx.args)  # number of arguments parsed without errors
        params = list(cmd.params)  # list all param names of the function

        param_name = params[successful_parsed_args]  # get name of the param where the error occurred
        param: Parameter = cmd.params[param_name]  # get inspect.Parameter object

        annotation = param.annotation  # get the class that the argument should be converted to

        object_name = annotation.__name__  # class name (e.g. 'Ticket' or 'TextChannel')

        msg = ctx.translate("[object] could not be found").format(object_name)
        await ctx.send(msg)

    elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
        msg = ctx.translate("parameter needs to be specified")
        await ctx.send(msg)

    else:
        raise error


@bot.before_invoke
async def before_invoke(ctx):
    await ctx.trigger_typing()


bot.load_extension('bot.commands')
