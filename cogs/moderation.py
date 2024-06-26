import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime
import aiosqlite

load_dotenv("../.env")


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.footer_text = "Made by Voidsudo"
        
    async def send_embed(self, ctx, title, description, color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x4863A0
        )
        embed.set_footer(text=self.footer_text)
        await ctx.respond(embed=embed)

    @discord.slash_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, reason: str = None):
        await ctx.defer()
        try:
            await member.ban(reason=reason)
            await self.send_embed(ctx, "Member Banned", f"{member.mention} was banned", discord.Color.red())
        except discord.Forbidden:
            await self.send_embed(ctx, "Error", "Need Higher Permissions", discord.Color.red())

    @discord.slash_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, reason: str = None):
        await ctx.defer()
        try:
            await member.kick(reason=reason)
            await self.send_embed(ctx, "Member Kicked", f"{member.mention} was kicked", discord.Color.orange())
        except discord.Forbidden:
            await self.send_embed(ctx, "Error", "Need Higher Permissions", discord.Color.red())

    @discord.slash_command(name="timeout", description="Timeout a member from the server.")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, reason: str = None):
        await ctx.defer(ephemeral=True)
        try:
            timeout_duration = discord.utils.utcnow() + datetime.timedelta(seconds=duration)
            await member.timeout(timeout_duration, reason=reason)

            if duration >= 60:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes} minutes and {seconds} seconds"
            else:
                duration_str = f"{duration} seconds"

            await self.send_embed(ctx, "Member Timed Out", f"{member.mention} was timed out for {duration_str}", discord.Color.blue())
        except discord.Forbidden:
            await self.send_embed(ctx, "Error", "Need Higher Permissions", discord.Color.red())
        except Exception as e:
            await self.send_embed(ctx, "Error", str(e), discord.Color.red())

    @commands.slash_command(name="unban", description="Unban a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User, reason: str = None):
        await ctx.defer()
        try:
            await ctx.guild.unban(member, reason=reason)
            await self.send_embed(ctx, "Member Unbanned", f"{member.mention} was unbanned", discord.Color.green())
        except discord.Forbidden:
            await self.send_embed(ctx, "Error", "Need Higher Permissions", discord.Color.red())
        except discord.NotFound:
            await self.send_embed(ctx, "Error", "Member not found or not banned", discord.Color.red())

    @commands.slash_command(name="untimeout", description="Unmute a member from the server.")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, reason: str = None):
        await ctx.defer(ephemeral=True)
        try:
            await member.remove_timeout(reason=reason)
            await self.send_embed(ctx, "Member Untimed Out", f"{member.mention} was untimeout", discord.Color.green())
        except discord.Forbidden:
            await self.send_embed(ctx, "Error", "Need Higher Permissions", discord.Color.red())
        except Exception as e:
            await self.send_embed(ctx, "Error", str(e), discord.Color.red())

            ## WARNING SYSTEM

    async def create_warn_table(self, guild_id):
        table_name = f"warns_{guild_id}"
        async with aiosqlite.connect("./db/warns.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (user_id INTEGER, reason TEXT)"
            )
            await db.commit()

    async def add_warn(self, guild_id, user_id, reason):
        table_name = f"warns_{guild_id}"
        async with aiosqlite.connect("./db/warns.db") as db:
            await db.execute(
                f"INSERT INTO {table_name} (user_id, reason) VALUES (?, ?)",
                (user_id, reason)
            )
            await db.commit()

    async def get_warns(self, guild_id, user_id):
        table_name = f"warns_{guild_id}"
        async with aiosqlite.connect("./db/warns.db") as db:
            async with db.execute(
                f"SELECT reason FROM {table_name} WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return rows

    warn = discord.SlashCommandGroup(name="warn", description="Warn commands")

    @warn.command(name="user", description="Warn a user")
    async def warn_user(self, ctx, user: discord.User, *, reason: str):
        await self.create_warn_table(ctx.guild.id)
        await self.add_warn(ctx.guild.id, user.id, reason)

        embed = discord.Embed(
            title="User Warned",
            description=f"{user.mention} has been warned for:\n{reason}",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed)

    @warn.command(name="list", description="List warnings for a user")
    async def warn_list(self, ctx, user: discord.User):
        await self.create_warn_table(ctx.guild.id)
        warns = await self.get_warns(ctx.guild.id, user.id)

        if warns:
            embed = discord.Embed(
                title=f"Warnings for {user.display_name}",
                color=discord.Color.orange()
            )
            for idx, warn in enumerate(warns, 1):
                embed.add_field(name=f"Warning {idx}", value=warn[0], inline=False)
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title=f"No Warnings",
                description=f"{user.display_name} has no warnings.",
                color=discord.Color.green()
            )
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Mod(bot))
