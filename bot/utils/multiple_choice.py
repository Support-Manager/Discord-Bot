import discord
import asyncio
from bot.properties import Defaults


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
