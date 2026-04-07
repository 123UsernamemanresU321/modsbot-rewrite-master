import os
import pickle

import discord
from discord.ext import commands

from cogs import config as cfg

Cog = commands.Cog
invites = {}

PERMANENT_INVITES = {"SxCN3xDDHs"}


class Invites(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global invites
        invites = {}

        path = "data/invites.p"
        if os.path.exists(path):
            with open(path, "rb") as f:
                temp = pickle.load(f)

            if isinstance(temp, dict):
                invites.update(temp)
            elif isinstance(temp, set):
                invites.update({code: 0 for code in temp})

        for code in PERMANENT_INVITES:
            invites.setdefault(code, 0)

    @commands.is_owner()
    @commands.command(aliases=["ui"])
    async def update_invites(self, ctx):
        inv_list = await ctx.guild.invites()
        for invite in inv_list:
            invites[invite.code] = invite.uses

        for code in PERMANENT_INVITES:
            invites.setdefault(code, 0)

        with open("data/invites.p", "wb") as f:
            pickle.dump(invites, f)

        await ctx.send("Invites updated.")

    @Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        invites[invite.code] = invite.uses or 0
        with open("data/invites.p", "wb") as f:
            pickle.dump(invites, f)

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        temp_invites = await member.guild.invites()

        possible_joins = set()
        for invite in temp_invites:
            old_uses = invites.get(invite.code, 0)
            if invite.uses > old_uses:
                possible_joins.add(invite)
            invites[invite.code] = invite.uses

        with open("data/invites.p", "wb") as f:
            pickle.dump(invites, f)

        possible_string = " ".join(
            f"{invite.code} by {invite.inviter.mention}" for invite in possible_joins
        )

        embed = discord.Embed()
        embed.add_field(name="User Joined", value=member.mention, inline=False)
        embed.add_field(
            name="Possible Invites",
            value=possible_string if possible_string else "None (probably Discovery)",
            inline=False,
        )

        join_delta = member.joined_at.timestamp() - member.created_at.timestamp()
        if join_delta > 1800:
            await member.guild.get_channel(cfg.Config.config["log_channel"]).send(
                embed=embed
            )
        else:
            embed.add_field(
                name="Recently Created",
                value=f"{join_delta} seconds ago",
                inline=False,
            )
            await self.bot.get_channel(cfg.Config.config["warn_channel"]).send(
                embed=embed
            )

        welcome_message = (
            f"Welcome to the Mathematical Olympiads Discord Server "
            f"<@!{member.id}>! Introduce yourself in "
            f"<#{cfg.Config.config['introduction_channel']}> "
            f"and enjoy your time here. 😃"
        )
        await self.bot.get_channel(cfg.Config.config["lounge_channel"]).send(
            welcome_message
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Invites(bot))
