import discord
from discord.ext import commands
import aiosqlite
import random
import time

class Exp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}
        self.xp_cooldown = 30  

    async def create_user_table(self, guild_id):
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/afk.db") as db:
            await db.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER, guild_id INTEGER, xp INTEGER, level INTEGER, PRIMARY KEY (id, guild_id))"
            )
            await db.commit()

    async def get_user_data(self, guild_id, user_id):
        await self.create_user_table(guild_id)
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/afk.db") as db:
            async with db.execute(
                f"SELECT xp, level FROM {table_name} WHERE id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    xp, level = row
                else:
                    xp, level = 0, 1
                    await db.execute(
                        f"INSERT INTO {table_name} (id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                        (user_id, guild_id, xp, level)
                    )
                    await db.commit()
                return xp, level

    async def add_experience(self, guild_id, user_id, xp):
        await self.create_user_table(guild_id)
        table_name = f"users_{guild_id}"
        async with aiosqlite.connect("./db/afk.db") as db:
            async with db.execute(
                f"SELECT xp, level FROM {table_name} WHERE id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    current_xp, current_level = row
                    required_xp = 100 * current_level  # XP required for the current level
                    new_xp = current_xp + xp
                    while new_xp >= required_xp:
                        new_xp -= required_xp
                        current_level += 1
                        required_xp = 500 * current_level
                    await db.execute(
                        f"UPDATE {table_name} SET xp = ?, level = ? WHERE id = ? AND guild_id = ?",
                        (new_xp, current_level, user_id, guild_id)
                    )
                else:
                    await db.execute(
                        f"INSERT INTO {table_name} (id, guild_id, xp, level) VALUES (?, ?, ?, ?)",
                        (user_id, guild_id, xp, 1)
                    )
            await db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        current_time = time.time()
        guild_id = message.guild.id
        user_id = message.author.id

        if user_id in self.cooldown and current_time - self.cooldown[user_id] < self.xp_cooldown:
            return
        
        xp_gain = random.randint(1, 10)
        await self.add_experience(guild_id, user_id, xp_gain)
        self.cooldown[user_id] = current_time

    exp = discord.SlashCommandGroup(name="exp", description="Experience points commands")

    @exp.command(name="add", description="Add experience points to a user")
    @commands.has_permissions(administrator=True)
    async def add_exp(self, ctx, member: discord.Member, amount: int):
        await ctx.defer()
        await self.add_experience(ctx.guild.id, member.id, amount)
        
        embed = discord.Embed(
            title="Experience Points Added",
            description=f"Added {amount} XP to {member.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        
        await ctx.respond(embed=embed)

    @exp.command(name="level", description="Get the level of a user")
    async def get_level(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        xp, level = await self.get_user_data(ctx.guild.id, member.id)
        
        embed = discord.Embed(
            title=f"Level Information for {member.display_name}",
            description=f"{member.display_name} is level {level} with {xp} XP",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        
        await ctx.respond(embed=embed)

    @exp.command(name="stats", description="Show your stats")
    async def stats(self, ctx):
        xp, level = await self.get_user_data(ctx.guild.id, ctx.author.id)
        
        embed = discord.Embed(
            title=f"Your Stats, {ctx.author.display_name}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    @exp.command(name="leaderboard", description="Show the leaderboard for XP and levels")
    async def leaderboard(self, ctx):
        table_name = f"users_{ctx.guild.id}"
        async with aiosqlite.connect("./db/afk.db") as db:
            async with db.execute(
                f"SELECT id, xp, level FROM {table_name} ORDER BY xp DESC LIMIT 10"
            ) as cursor:
                leaderboard_data = await cursor.fetchall()
        
        embed = discord.Embed(
            title="Leaderboard: XP and Levels",
            color=discord.Color.gold()
        )

        if not leaderboard_data:
            embed.description = "No data available."
        else:
            for idx, (user_id, xp, level) in enumerate(leaderboard_data, start=1):
                member = ctx.guild.get_member(user_id)
                if member:
                    embed.add_field(
                        name=f"#{idx}: {member.display_name}",
                        value=f"Level **{level}** with **{xp}** XP",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"#{idx}: User ID {user_id}",
                        value=f"Level **{level}** with **{xp}** XP",
                        inline=False
                    )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Exp(bot))