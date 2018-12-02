import discord
import asyncio
from bot.properties import Defaults


class Confirmation:
    """ Represents a message to let the user confirm a specific action. """

    def __init__(self, ctx):
        self._ctx = ctx
        self.emojis = {"✅": True, "❌": False}
        self._confirmed = None
        self._message = None

    @property
    def confirmed(self):
        return self._confirmed

    async def confirm(self, text: str) -> bool or None:
        emb = discord.Embed(
            title=text,
            color=Defaults.COLOR
        )
        emb.set_author(
            name=str(self._ctx.author),
            icon_url=self._ctx.author.avatar_url
        )

        msg = await self._ctx.send(embed=emb)
        self._message = msg

        for emoji in self.emojis:
            await msg.add_reaction(emoji)

        author = self._ctx.author

        try:
            reaction, user = await self._ctx.bot.wait_for(
                'reaction_add',
                check=lambda r, u: (r.message.id == msg.id) and (u.id == author.id) and (r.emoji in self.emojis),
                timeout=20
            )
        except asyncio.TimeoutError:
            self._confirmed = None
            return
        finally:
            await msg.clear_reactions()

        confirmed = self.emojis[reaction.emoji]

        self._confirmed = confirmed
        return confirmed

    async def display(self, text: str, embed: discord.Embed=None):
        await self._message.edit(content=text, embed=embed)
