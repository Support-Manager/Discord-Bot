import logging
import sys
import traceback
import os
import time
import discord
from discord.ext import commands
from ruamel import yaml
from .models import Guild, User, graph, Ticket, Response
from .properties import CONFIG, Defaults
from .errors import MissingPermissions, InvalidAction
from . import utils
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
    def db_author(self):
        return User.from_discord_user(self.author, ctx=self)

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
async def on_member_join(member):
    db_guild = Guild.from_discord_guild(member.guild)
    db_user = User.from_discord_user(member)

    db_guild.joined_users.add(db_user, properties={'UTC': time.time()})

    db_guild.push()


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

    elif isinstance(error, discord.ext.commands.MissingPermissions) or isinstance(error, MissingPermissions):
        msg = ctx.translate("you are not allowed to perform this action")
        await ctx.send(msg)

    elif isinstance(error, discord.ext.commands.BotMissingPermissions):
        msg = ctx.translate("need required permissions [permissions]").format("`, `".join(error.missing_perms))
        await ctx.send(msg)

    elif isinstance(error, InvalidAction):
        msg = ctx.translate("invalid action")
        await ctx.send(msg)

    elif isinstance(error, discord.ext.commands.CommandNotFound):
        pass

    else:
        raise error


@bot.event
async def on_error(event, *args, **kwargs):
    exc_info = sys.exc_info()
    instance = exc_info[1]

    if event == "on_voice_state_update":
        member = args[0]
        guild = Guild.from_discord_guild(member.guild)

        translator = utils.Translator(bot.string_translations, guild.language_enum)

        if isinstance(instance, errors.OnCooldown):
            seconds = int(instance.retry_after)
            try:
                await member.send(translator.translate("you're on cooldown for [sec] seconds").format(seconds))
            except discord.Forbidden:
                pass

        elif isinstance(instance, discord.Forbidden) and guild.log_channel is not None:
            await guild.log(translator.translate("not enough permissions to perform action"))

    else:
        print('Ignoring exception in {}'.format(event), file=sys.stderr)
        traceback.print_exc()


@bot.before_invoke
async def before_invoke(ctx):
    await ctx.trigger_typing()


bot.load_extension('bot.commands')
bot.load_extension('bot.services')
