from discord.ext import commands


class SupportManagerError(commands.CommandError):
    """ Support-Manager's base exception. """

    def __init__(self, msg=None):
        super(SupportManagerError, self).__init__(msg)


class MissingPermissions(SupportManagerError):
    pass


class InvalidAction(SupportManagerError):
    pass
