import discord
import asyncio
from copy import deepcopy


class EmbedPaginator:
    """ Represents an interactive menu containing multiple embeds. """

    def __init__(self, ctx, pages: [discord.Embed]):
        self._ctx = ctx
        self.pages = pages

        self.control_emojis = ('⏮', '◀', '▶', '⏭', '⏹')

    @property
    def formatted_pages(self):
        pages = deepcopy(self.pages)  # copy by value not reference
        for page in pages:
            page.set_footer(
                text=self._ctx.translate("page") + f" ( {pages.index(page)+1} | {len(pages)} )"
            )
        return pages

    async def run(self):
        if len(self.pages) == 1:  # no pagination needed in this case
            await self._ctx.send(embed=self.pages[0])
            return

        message = await self._ctx.send(embed=self.formatted_pages[0])
        current_page_index = 0

        for emoji in self.control_emojis:
            await message.add_reaction(emoji)

        def check(r: discord.Reaction, u: discord.User):
            res = (r.message.id == message.id) and (u.id == self._ctx.author.id) and (r.emoji in self.control_emojis)
            return res

        while True:
            try:
                reaction, user = await self._ctx.bot.wait_for('reaction_add', check=check, timeout=100)
            except asyncio.TimeoutError:
                await message.clear_reactions()
                return

            emoji = reaction.emoji
            max_index = len(self.pages) - 1  # index for the last page

            if emoji == self.control_emojis[0]:
                load_page_index = 0

            elif emoji == self.control_emojis[1]:
                load_page_index = current_page_index - 1 if current_page_index > 0 else current_page_index

            elif emoji == self.control_emojis[2]:
                load_page_index = current_page_index + 1 if current_page_index < max_index else current_page_index

            elif emoji == self.control_emojis[3]:
                load_page_index = max_index

            else:
                await message.delete()
                return

            await message.edit(embed=self.formatted_pages[load_page_index])
            await message.remove_reaction(reaction, user)

            current_page_index = load_page_index

    @staticmethod
    def generate_sub_lists(l: list) -> [list]:
        if len(l) > 25:
            sub_lists = []

            while len(l) > 20:
                sub_lists.append(l[:20])
                del l[:20]

            sub_lists.append(l)

        else:
            sub_lists = [l]

        return sub_lists
