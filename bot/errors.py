from discord.ext import commands


class SupportManagerError(Exception):
    """ Support-Manager's base exception. """

    def __init__(self, msg=None):
        super(SupportManagerError, self).__init__(msg)


class SupportManagerCommandError(commands.CommandError):
    pass


class MissingPermissions(SupportManagerCommandError):
    pass


class InvalidAction(SupportManagerCommandError):
    pass


class OnCooldown(SupportManagerError):
    def __init__(self, cooldown, retry_after, msg=None):
        self.cooldown = cooldown
        self.retry_after = retry_after
        super().__init__(msg=msg)
