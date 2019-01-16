from bot import Defaults, checks
from bot.models import User
from discord.ext import commands
import discord
import time
from datetime import date


@commands.command(aliases=["stats"])
@commands.guild_only()
@checks.prime_feature()
async def statistics(ctx, user: User=None):
    stats_emb = discord.Embed(
        title=ctx.translate("statistics"),
        color=Defaults.COLOR
    )

    def get_local(properties: iter):
        def is_local(p):
            return p.guild.id == ctx.guild.id

        return [p for p in properties if is_local(p)]

    if user is not None:
        global_warnings = len(user.warnings)
        local_warnings = len(get_local(user.warnings))

        global_kicked = len(user.kicks)
        local_kicked = len(get_local(user.kicks))

        global_banned = len(user.bans)
        local_banned = len(get_local(user.bans))

        global_created_tickets = len(user.tickets)
        local_created_tickets = len(get_local(user.tickets))

        has_reported = len(get_local(user.issued_reports))
        reported_by = len(get_local(user.reports))

        global_created_responses = len(user.responses)
        local_created_responses = len(get_local(user.responses))

        shared_guilds = len([g for g in ctx.bot.guilds if user.id in [m.id for m in g.members]])

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
            name=ctx.translate("reports"),
            value=f"{ctx.translate('has reported')}: `{has_reported}`\n{ctx.translate('was reported')}: `{reported_by}`"
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

        class Stats:
            def __init__(self, name: str, relationships: iter, utc_key: callable):
                self.name = name
                self.relationships = relationships
                self.get_timestamp = utc_key

            @property
            def total(self) -> int:
                return len(self.relationships)

            @property
            def last_30_days(self) -> int:
                return len([r for r in self.relationships if self.get_timestamp(r) > time.time() - (60 * 60 * 24 * 30)])

            @property
            def average_per_day(self) -> float:
                dates = list(map(lambda r: date.fromtimestamp(self.get_timestamp(r)), self.relationships))
                day_count = ((date.today() - min(dates)).days + 1) if len(dates) != 0 else 1
                return len(self.relationships) / day_count

            def add_field(self) -> None:
                stats_emb.add_field(
                    name=ctx.translate(self.name),
                    value=f"{ctx.translate('total')}: `{self.total}`\n"
                          f"{ctx.translate('last 30 days')}: `{self.last_30_days}`\n"
                          f"{ctx.translate('average per day')}: `{round(self.average_per_day, 2)}`"
                )

        member_joins = Stats("member joins", guild.joined_users, lambda m: guild.joined_users.get(m, 'UTC'))
        member_joins.add_field()

        tickets = Stats("tickets", guild.tickets, lambda t: t.created_by.get(list(t.created_by)[0], 'UTC'))
        tickets.add_field()

        warnings = Stats("warned", guild.warnings, lambda w: w.utc)
        warnings.add_field()

        kicked = Stats("kicked", guild.kicks, lambda k: k.utc)
        kicked.add_field()

        banned = Stats("banned", guild.bans, lambda b: b.utc)
        banned.add_field()

        stats_emb.set_footer(text=ctx.translate("recorded since the bot is member"))

    await ctx.send(embed=stats_emb)
