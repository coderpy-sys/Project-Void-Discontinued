import discord
from discord.ext import commands
import aiosqlite
import datetime

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        async with aiosqlite.connect("./db/database.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    coins INTEGER NOT NULL,
                    weekly_timestamp INTEGER NOT NULL,
                    daily_timestamp INTEGER NOT NULL
                )
            """)
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
                user = await cursor.fetchone()
                if user is None:
                    await db.execute(
                        "INSERT INTO users (id, coins, weekly_timestamp, daily_timestamp) VALUES (?, ?, ?, ?)",
                        (user_id, 0, 0, 0),
                    )
                    await db.commit()
                    return {
                        "coins": 0,
                        "weekly_timestamp": 0,
                        "daily_timestamp": 0
                    }
                else:
                    return {
                        "coins": user[1],
                        "weekly_timestamp": user[2],
                        "daily_timestamp": user[3]
                    }

    economy = discord.SlashCommandGroup(name="economy", description="Economy commands")

    @economy.command(name="daily", description="Claim your daily reward")
    async def daily(self, ctx):
        user = await self.get_user(ctx.author.id)
        now = round(datetime.datetime.now().timestamp())

        if user["daily_timestamp"] == 0 or user["daily_timestamp"] + 86400 <= now:
            async with aiosqlite.connect("./db/database.db") as db:
                await db.execute(
                    "UPDATE users SET coins = coins + 100, daily_timestamp = ? WHERE id = ?",
                    (now, ctx.author.id),
                )
                await db.commit()
            embed = discord.Embed(
                title="Daily Reward",
                description="You have claimed your daily reward!",
                color=discord.Color.green()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
        else:
            wait_time = user["daily_timestamp"] + 86400 - now
            embed = discord.Embed(
                title="Daily Reward",
                description=f"You have already claimed your daily reward! Wait <t:{user['daily_timestamp'] + 86400}:R> to claim again.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)

    @economy.command(name="weekly", description="Claim your weekly reward")
    async def weekly(self, ctx):
        user = await self.get_user(ctx.author.id)
        now = round(datetime.datetime.now().timestamp())

        if user["weekly_timestamp"] == 0 or user["weekly_timestamp"] + 604800 <= now:
            async with aiosqlite.connect("./db/database.db") as db:
                await db.execute(
                    "UPDATE users SET coins = coins + 700, weekly_timestamp = ? WHERE id = ?",
                    (now, ctx.author.id),
                )
                await db.commit()
            embed = discord.Embed(
                title="Weekly Reward",
                description="You have claimed your weekly reward!",
                color=discord.Color.green()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)
        else:
            wait_time = user["weekly_timestamp"] + 604800 - now
            embed = discord.Embed(
                title="Weekly Reward",
                description=f"You have already claimed your weekly reward! Wait <t:{user['weekly_timestamp'] + 604800}:R> to claim again.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.respond(embed=embed)

    @economy.command(name="balance", description="Check your balance")
    async def balance(self, ctx, user: discord.Member = None):
        target_user = user if user else ctx.author
        user_data = await self.get_user(target_user.id)
        embed = discord.Embed(
              title=f"{target_user.name}'s Balance",
              description=f"You have {user_data['coins']} coins",
              color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=target_user.avatar.url)
        await ctx.respond(embed=embed)

    @economy.command(name="help", description="Get help with economy commands")
    async def e_help(self, ctx):
        embed = discord.Embed(
            title="Economy Help",
            description="**/economy daily** - Claim your daily reward\n**/economy weekly** - Claim your weekly reward\n**/economy balance** - Check your balance",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)

    @economy.command(name="leaderboard", description="Show the Richest users")
    async def leaderboard(self, ctx):
        async with aiosqlite.connect("./db/database.db") as db:
            async with db.execute("SELECT * FROM users ORDER BY coins DESC LIMIT 10") as cursor:
                users = await cursor.fetchall()
                embed = discord.Embed(
                    title="Economy Leaderboard", description="", color=discord.Color.blue()
                )
                for idx, user in enumerate(users, start=1):
                    member = ctx.guild.get_member(user[0])
                    if member:
                        embed.add_field(
                            name=f"#{idx}: {member.display_name}",
                            value=f"**{user[1]}** Coins",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name=f"#{idx}: User: {user[0]}",
                            value=f"**{user[1]}** Coins",
                            inline=False
                        )
                embed.set_footer(text="Requested by " + ctx.author.display_name, icon_url=ctx.author.avatar.url)
                await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Economy(bot))