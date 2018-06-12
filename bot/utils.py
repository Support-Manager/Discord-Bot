import discord
from neo4j_connection import *
import json
import logging
import sys
import time
import asyncio
from copy import deepcopy

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
logger.addHandler(console)

with open('properties/secrets.json', 'r', encoding='utf-8') as s:
    SECRETS = json.load(s)

graph = Graph(password=SECRETS['neo4j'])  # represents database connection


with open('properties/default.json', 'r', encoding='utf-8') as d:
    DEFAULT = json.load(d)


with open('properties/config.json', 'r', encoding='utf-8') as c:
    CONFIG = json.load(c)

    EMBED_COLOR = int(CONFIG["embed_color"], 16)  # convert hex string to integer
    BOT_ADMINS = CONFIG["bot_admins"]


async def dynamic_prefix(bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return DEFAULT['prefix']

    guild = Guild()
    guild.id = msg.guild.id
    graph.pull(guild)

    return guild.prefix


def get_guild(guild: discord.Guild):
    g = Guild.select(graph, guild.id).first()

    if g is None:
        g = Guild()

        g.id = guild.id
        g.prefix = DEFAULT['prefix']
        g.default_scope = DEFAULT['scope']
        g.language = DEFAULT['language']

        graph.create(g)
        logger.info(f"Added guild to database: {g.id}")

    return g


def get_user(user: discord.User):
    u = User.select(graph, user.id).first()

    if u is None:
        u = User()

        u.id = user.id

        graph.create(u)
        logger.info(f"Added user to database: {u.id}")

    return u


def ticket_embed(ctx, t: Ticket):
    author = ctx.bot.get_user(t.author.id)
    guild = ctx.bot.get_guild(t.guild.id)

    emb = discord.Embed(
        title=t.title,
        description=t.description,
        color=EMBED_COLOR
    )
    emb.add_field(
        name="ID",
        value=t.id
    )
    emb.add_field(
        name="Guild",
        value=guild
    )
    emb.add_field(
        name="Scope",
        value=t.scope
    )
    emb.add_field(
        name="State",
        value=t.state
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
        color=EMBED_COLOR
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
            await channel.send(f"{message} {mention}", embed=ticket_embed(ctx.bot, ticket))
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


def is_author_or_supporter(ctx, entry: Ticket or Response):
    return entry.guild.support_role in [role.id for role in ctx.author.roles] or ctx.author.id == entry.author.id or \
        ctx.author.permissions_in(ctx.channel).administrator or ctx.author.id in BOT_ADMINS


def escaped(msg: str):
    """ Escaping code blocks and double line breaks. """
    return msg.replace("`", "'").replace("\n\n", " ")


Message = discord.Message


async def multiple_choice(ctx, options: list, title: str, description: str="", message: Message=None) -> (str, Message):
    config_embed = discord.Embed(
        title=title,
        description=description + "\n" + ctx.translate("use :x: to close the dialog"),
        color=EMBED_COLOR
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
        self.response_embeds = [response_embed(self._ctx, r) for r in sorted(self.ticket.responses, key=lambda r: r.id)]

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
