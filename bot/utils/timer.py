import asyncio
from bot.models import Guild


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
    def __init__(self, ctx, days, member, reason=None):
        timeout = days * (60*60*24)  # calculates days into seconds

        async def callback(c, m, *, r):
            await m.unban(reason=r)

            g = Guild.from_discord_guild(m.guild)
            await g.log(c.translate("unbanned [member] [reason]").format(str(m), reason))

        super().__init__(timeout, callback, ctx, member, r=reason)
