import asyncio


class Timer:
    def __init__(self, timeout, callback, *cb_args, **cb_kwargs):
        self._timeout = timeout
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback(*self._cb_args, **self._cb_kwargs)

    def cancel(self):
        self._task.cancel()


class UnbanTimer(Timer):
    def __init__(self, ctx, days, user, reason=None):
        timeout = days * (60*60*24)  # calculates days into seconds

        async def callback(c, u, *, r):
            await c.guild.unban(u, reason=r)

            g = await ctx.db_guild
            await g.log(c.translate("unbanned [member] [reason]").format(str(u), reason))

        super().__init__(timeout, callback, ctx, user, r=reason)
