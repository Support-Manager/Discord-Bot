from bot.errors import MissingPermissions
from bot.models import Ticket, Response
from bot.context import Context
from typing import Union
from functools import wraps


def requires_property_access(f: callable):
    @wraps(f)
    async def wrapper(ctx: Context, prop: Union[Ticket, Response], *args, **kwargs):
        if await ctx.may_fully_access(prop):
            await f(ctx, prop, *args, **kwargs)
        else:
            raise MissingPermissions

    return wrapper
