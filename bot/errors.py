class SupportManagerError(Exception):
    """ Support-Manager's base exception. """

    def __init__(self, msg=None):
        super(SupportManagerError, self).__init__(msg)


class MissingPermissions(SupportManagerError):
    pass
