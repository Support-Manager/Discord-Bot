from bot import bot, Defaults
from bot.models import User, UserMixin
from discord.ext import commands
import discord
import time
from datetime import date


@bot.command(aliases=["stats"])
@commands.guild_only()
async def statistics(ctx, user: User=None):
    stats_emb = discord.Embed(
        title=ctx.translate("statistics"),
        color=Defaults.COLOR
    )

    def get_local(properties: iter, guild_as_property=True):
        def is_local(p):
            if guild_as_property:
                return p.guild.id == ctx.guild.id
            else:  # guild as relationship property
                return properties.get(p, 'guild') == ctx.guild.id

        return [p for p in properties if is_local(p)]

    if user is not None:
        global_warnings = len(user.warned_by)
        local_warnings = len(get_local(user.warned_by, guild_as_property=False))

        global_kicked = len(user.kicked_by)
        local_kicked = len(get_local(user.kicked_by, guild_as_property=False))

        global_banned = len(user.banned_by)
        local_banned = len(get_local(user.banned_by, guild_as_property=False))

        global_created_tickets = len(user.tickets)
        local_created_tickets = len(get_local(user.tickets))

        global_created_responses = len(user.responses)
        local_created_responses = len(get_local(user.responses))

        shared_guilds = len([g for g in bot.guilds if user.id in [m.id for m in g.members]])

        stats_emb.description = ctx.translate("statistics of the given user")

        stats_emb.set_author(
            name=str(user.discord),
            icon_url=user.discord.avatar_url
        )

        def format_values(global_value, local_value):
            return f"{ctx.translate('global')}: `{global_value}`\n{ctx.translate('local')}: `{local_value}`"

        stats_emb.add_field(
            name=ctx.translate("warned"),
            value=format_values(global_warnings, local_warnings)
        )
        stats_emb.add_field(
            name=ctx.translate("kicked"),
            value=format_values(global_kicked, local_kicked)
        )
        stats_emb.add_field(
            name=ctx.translate("banned"),
            value=format_values(global_banned, local_banned)
        )
        stats_emb.add_field(
            name=ctx.translate("tickets"),
            value=format_values(global_created_tickets, local_created_tickets)
        )
        stats_emb.add_field(
            name=ctx.translate("responses"),
            value=format_values(global_created_responses, local_created_responses)
        )
        stats_emb.add_field(
            name=ctx.translate("shared guilds"),
            value=f"`{shared_guilds}`"
        )

    else:
        guild = ctx.db_guild

        stats_emb.description = ctx.translate("statistics of this guild")

        stats_emb.set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        )

        online_members = [m for m in ctx.guild.members if m.status == discord.Status.online]
        stats_emb.add_field(
            name=ctx.translate("members"),
            value=f"{ctx.translate('total')}: `{ctx.guild.member_count}`\n"
                  f"{ctx.translate('online')}: `{len(online_members)}`"
        )

        class TimeGetter:
            def __init__(self, relationships: iter, property_key: str=None):
                """ property_key: name of the relationship which contains the utc timestamp """

                self.relationships = relationships
                self.property_key = property_key

            def __call__(self, r):
                if self.property_key is None:
                    return self.relationships.get(r, 'UTC')
                else:
                    property_relations = getattr(r, self.property_key)
                    return property_relations.get(list(property_relations)[0], 'UTC')

        class OutlawTimeGetter:
            def __init__(self, property_key: str):
                self.db_members: [User] = [User.from_discord_user(m, ctx) for m in ctx.guild.members]
                self.member_warnings: {User: [UserMixin]} = {
                    m.id: (m, get_local(getattr(m, property_key), guild_as_property=False)) for m in self.db_members
                }
                self.warning_times: [float] = [
                    getattr(self.member_warnings[m1_id][0], property_key).get(m2, 'UTC')
                    for m1_id in self.member_warnings for m2 in self.member_warnings[m1_id][1]
                ]

            def __call__(self, r: float):
                return r

        class Stats:
            def __init__(self, name: str, relationships: iter, property_key: str=None):
                self.name = name
                self.relationships = relationships
                self.get_time = TimeGetter(relationships, property_key=property_key)

            @property
            def total(self) -> int:
                return len(self.relationships)

            @property
            def last_30_days(self) -> int:
                return len([r for r in self.relationships if self.get_time(r) > time.time() - (60 * 60 * 24 * 30)])

            @property
            def average_per_day(self) -> float:
                dates = list(map(lambda r: date.fromtimestamp(self.get_time(r)), self.relationships))
                day_count = ((date.today() - min(dates)).days + 1) if len(dates) != 0 else 1
                return len(self.relationships) / day_count

            def add_field(self) -> None:
                stats_emb.add_field(
                    name=ctx.translate(self.name),
                    value=f"{ctx.translate('total')}: `{self.total}`\n"
                          f"{ctx.translate('last 30 days')}: `{self.last_30_days}`\n"
                          f"{ctx.translate('average per day')}: `{round(self.average_per_day, 2)}`"
                )

        member_joins = Stats("member joins", guild.joined_users)
        member_joins.add_field()

        tickets = Stats("tickets", guild.tickets, "created_by")
        tickets.add_field()

        get_warning_time = OutlawTimeGetter("warned_by")
        warnings = Stats("warned", get_warning_time.warning_times)
        warnings.get_time = get_warning_time
        warnings.add_field()

        get_kick_time = OutlawTimeGetter("kicked_by")
        kicked = Stats("kicked", get_kick_time.warning_times)
        kicked.get_time = get_kick_time
        kicked.add_field()

        get_ban_time = OutlawTimeGetter("banned_by")
        banned = Stats("banned", get_ban_time.warning_times)
        banned.get_time = get_ban_time
        banned.add_field()

        stats_emb.set_footer(text=ctx.translate("recorded since the bot is member"))

    await ctx.send(embed=stats_emb)
