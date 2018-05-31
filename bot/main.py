from bot.utils import *
from bot.subclasses import Bot

bot = Bot(command_prefix=dynamic_prefix, pm_help=None, case_insensitive=True)

bot.remove_command('help')


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name}")

    for guild in bot.guilds:
        get_guild(guild)

    await bot.change_presence(activity=discord.Game(name="/help"))


@bot.event
async def on_guild_join(guild):
    get_guild(guild)


@bot.before_invoke
async def before_invoke(ctx):
    await ctx.trigger_typing()


bot.load_extension('commands')

bot.run(SECRETS['token'])
