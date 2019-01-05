from bot import errors, CONFIG
from inspect import Parameter
from discord.ext import commands
import discord


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

    elif isinstance(error, discord.ext.commands.MissingPermissions) or isinstance(error, errors.MissingPermissions):
        msg = ctx.translate("you are not allowed to perform this action")
        await ctx.send(msg)

    elif isinstance(error, discord.ext.commands.BotMissingPermissions):
        msg = ctx.translate("need required permissions [permissions]").format("`, `".join(error.missing_perms))
        await ctx.send(msg)

    elif isinstance(error, errors.InvalidAction):
        msg = ctx.translate("invalid action")
        await ctx.send(msg)

    elif isinstance(error, errors.Blacklisted):
        msg = ctx.translate("you are blacklisted")
        await ctx.send(msg)

    elif isinstance(error, errors.RequiresPrime):
        await ctx.send(ctx.translate("this is a prime feature").format(CONFIG['prime_url']))

    elif isinstance(error, discord.ext.commands.CommandNotFound):
        pass

    else:
        raise error
