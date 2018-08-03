import discord
import time
import asyncio
from copy import deepcopy
from .models import Ticket, Response
from .properties import Defaults
from bot import enums


def ticket_embed(ctx, t: Ticket):
    author = ctx.bot.get_user(t.author.id)

    emb = discord.Embed(
        title=t.title,
        description=t.description,
        color=Defaults.COLOR
    )
    emb.add_field(
        name="ID",
        value=t.channel.mention if t.scope_enum == enums.Scope.CHANNEL else t.id
    )
    emb.add_field(
        name="Scope",
        value=t.scope
    )
    emb.add_field(
        name="State",
        value=t.state
    )

    if isinstance(ctx.channel, discord.DMChannel):  # only need to display guild in DM channels
        emb.add_field(
            name="Guild",
            value=t.guild.discord.name
        )

    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    creation_time = t.created_by.get(t.author, 'UTC')
    creation_gmtime = time.gmtime(creation_time)

    if creation_gmtime.tm_yday > time.gmtime().tm_yday or creation_gmtime.tm_year > time.gmtime().tm_year:
        emb.add_field(
            name=ctx.translate("created on"),
            value=time.strftime("%B %d, %Y", time.gmtime(creation_time))
        )

    if creation_time < t.updated:
        emb.set_footer(
            text=time.strftime(f"{ctx.translate('updated on')} %B %d, %Y at %I:%M %P UTC", time.gmtime(t.updated))
        )

    return emb


def response_embed(ctx, r: Response):
    author = ctx.bot.get_user(r.author.id)
    guild = ctx.bot.get_guild(r.guild.id)

    emb = discord.Embed(
        title=f"Re: {r.ticket.title}",
        description=r.content,
        color=Defaults.COLOR
    )
    emb.add_field(
        name="ID",
        value=r.id
    )
    emb.add_field(
        name="Guild",
        value=guild
    )
    emb.add_field(
        name=ctx.translate("refers to ticket"),
        value=f"#{r.ticket.id}"
    )
    emb.set_author(
        name=f"{author.name}#{author.discriminator}",
        icon_url=author.avatar_url
    )

    creation_time = r.created_by.get(r.author, 'UTC')
    creation_gmtime = time.gmtime(creation_time)

    if creation_gmtime.tm_yday > time.gmtime().tm_yday or creation_gmtime.tm_year > time.gmtime().tm_year:
        emb.add_field(
            name="Created on",
            value=time.strftime("%B %d, %Y", time.gmtime(creation_time))
        )

    """
    if creation_time < t.updated:
        emb.set_footer(
            text=time.strftime("Updated on %B %d, %Y at %I:%M %P UTC", time.gmtime(t.updated))
        )
    """

    return emb


async def notify_supporters(ctx, message, ticket: Ticket, embed=True):
    guild = ticket.guild

    channel_id = guild.channel
    if (channel_id is not None) and (ticket.scope != 'public') and (channel_id != ctx.channel.id):
        channel = ctx.bot.get_channel(channel_id)

        mention = ""

        if guild.support_role is not None:
            role = discord.utils.find(lambda r: r.id == guild.support_role, ctx.guild.roles)
            if role is not None:
                mention = role.mention

        if embed:
            await channel.send(f"{message} {mention}", embed=ticket_embed(ctx, ticket))
        else:
            await channel.send(f"{message} {mention}")


async def notify_author(ctx, message, ticket: Ticket, embed=None):
    """ This is to notify a ticket author on specific events. """

    # It's not necessary to inform the author when the action was triggered by himself.
    if not ctx.author.id == ticket.author.id:
        try:
            member = ctx.guild.get_member(ticket.author.id)
            await member.send(message, embed=embed)
            return 0

        except discord.Forbidden:  # if a user has DMs disabled
            return 1


def escaped(msg: str):
    """ Escaping code blocks and double line breaks. """
    return msg.replace("`", "'").replace("\n\n", " ")


Message = discord.Message


async def multiple_choice(ctx, options: list, title: str, description: str="", message: Message=None) -> (str, Message):
    config_embed = discord.Embed(
        title=title,
        description=description + "\n" + ctx.translate("use :x: to close the dialog"),
        color=Defaults.COLOR
    )

    emojis = []
    for i in range(len(options)):  # generates unicode emojis and embed-fields
        hex_str = hex(224 + (6 + i))[2:]
        emoji = b'\\U0001f1a'.replace(b'a', bytes(hex_str, "utf-8"))
        emoji = emoji.decode("unicode-escape")
        emojis.append(emoji)

        config_embed.add_field(
            name=emoji,
            value=options[i],
            inline=False
        )

    if message is None:
        message = await ctx.send(embed=config_embed)
    else:
        await message.clear_reactions()
        await message.edit(content=None, embed=config_embed)

    for emoji in emojis:
        await message.add_reaction(emoji)

    close_emoji = '❌'
    await message.add_reaction(close_emoji)

    def check(r, u):
        res = (r.message.id == message.id) and (u.id == ctx.author.id) and (r.emoji in emojis or r.emoji == close_emoji)
        return res

    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', check=check, timeout=60)
    except asyncio.TimeoutError:
        return None, message

    if reaction.emoji == close_emoji:
        return None, message

    index = emojis.index(reaction.emoji)
    return options[index], message


class TicketViewer:
    """ Represents an interactive menu containing the whole data of a ticket (including responses). """

    def __init__(self, ctx, ticket: Ticket):
        self._ctx = ctx
        self.ticket = ticket
        self.ticket_embed = ticket_embed(self._ctx, self.ticket)
        self.response_embeds = \
            [response_embed(self._ctx, r) for r in sorted(self.ticket.get_responses(), key=lambda r: r.id)]

        self.pages = []
        self.pages.append(deepcopy(self.ticket_embed))  # copy by value (not reference)
        self.pages.extend(self.response_embeds)

        self.control_emojis = ('⏮', '◀', '▶', '⏭', '⏹')

        for page in self.pages:
            page.set_footer(text=ctx.translate("page") + f" ( {self.pages.index(page)+1} | {len(self.pages)} )")

    async def run(self):
        if len(self.pages) == 1:
            await self._ctx.send(embed=self.ticket_embed)
            return

        message = await self._ctx.send(embed=self.pages[0])
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
            max_index = len(self.pages) - 1

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

            await message.edit(embed=self.pages[load_page_index])
            await message.remove_reaction(reaction, user)

            current_page_index = load_page_index


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
