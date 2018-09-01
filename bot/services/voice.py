import discord
from bot import bot, errors
from bot.models import Guild
from bot.utils import notify_supporters, Translator
from discord.ext.commands import Cooldown, CooldownMapping, BucketType


async def leaved_channel(channel, guild, translator):
    category = channel.category

    if category is not None:
        if category.id == guild.voice_category:
            if len(channel.members) == 0:
                """ when the channel is empty now """

                channels_occupied = [len(c.members) >= 1 for c in category.channels]

                if channels_occupied.count(True) == len(category.channels) - 1:
                    """ when all other channels are occupied """

                    await channel.edit(
                        name=translator.translate("available support room"),
                        reason=translator.translate("providing available voice support room")
                    )

                else:
                    await channel.delete(reason=translator.translate("support room is not needed anymore"))


class CustomCooldownMapping(CooldownMapping):
    def _bucket_key(self, member):
        bucket_type = self._cooldown.type
        if bucket_type is BucketType.user:
            return member.id
        elif bucket_type is BucketType.guild:
            return member.guild.id
        elif bucket_type is BucketType.channel:
            return member.voice.channel.id


cooldown = Cooldown(1, 300, BucketType.user)
buckets = CustomCooldownMapping(cooldown)


@bot.event
async def on_voice_state_update(member, before, after):
    guild = Guild.from_discord_guild(member.guild)

    translator = Translator(bot.string_translations, guild.language_enum)

    if after.channel is not None:
        channel = after.channel
        category = channel.category

        if category is not None:
            if before.channel != channel and category.id == guild.voice_category:
                """ when someone joins into a server's voice support channel """

                if len(channel.members) == 1:
                    await channel.edit(
                        name=translator.translate("occupied support room"),
                        reason=translator.translate("support room got occupied")
                    )

                    new_channel = await member.guild.create_voice_channel(
                        name=translator.translate("available support room"),
                        category=category,
                        reason=translator.translate("providing available voice support room")
                    )
                    await new_channel.edit(user_limit=2)

                    if buckets.valid:
                        bucket = buckets.get_bucket(member)  # getting cooldown
                        retry_after = bucket.update_rate_limit()
                        if retry_after:
                            if before.channel is not None:
                                await leaved_channel(before.channel, guild, translator)

                            raise errors.OnCooldown(bucket, retry_after)

                    message = translator.translate("[user] is waiting for support in [channel]")
                    await notify_supporters(bot, message.format(member.mention, category.name), guild)

                    message = translator.translate("the supporters have been notified")
                    try:
                        await member.send(message)
                    except discord.Forbidden:
                        pass

    if before.channel is not None:
        channel = before.channel

        await leaved_channel(channel, guild, translator)
